from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from app.models.usuario import Usuario
from app.models.token_refresco import TokenRefresco
from app.repositories.usuario import UsuarioRepository
from app.repositories.token_refresco import TokenRefrescoRepository
from app.schemas.auth import Token, Enroll2FAResponse
from app.core.security import verify_password, hash_password, create_access_token, decode_access_token
from app.core.config import Settings
from jose import jwt
import secrets
import hmac
import hashlib
import time
import struct
import base64
from collections import defaultdict

class RateLimiter:
    def __init__(self, limit: int = 5, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._history = defaultdict(list)

    def check_rate_limit(self, ip: str, email: str) -> bool:
        now = time.time()
        key = (ip, email.lower().strip())
        self._history[key] = [t for t in self._history[key] if now - t < self.window_seconds]
        if len(self._history[key]) >= self.limit:
            return False
        self._history[key].append(now)
        return True

login_rate_limiter = RateLimiter(limit=5, window_seconds=60)

def generate_totp_secret() -> str:
    random_bytes = secrets.token_bytes(20)
    return base64.b32encode(random_bytes).decode('utf-8').replace('=', '')

def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    try:
        secret = secret.upper().replace(" ", "")
        missing_padding = len(secret) % 8
        if missing_padding:
            secret += '=' * (8 - missing_padding)
        key = base64.b32decode(secret)
        
        now = int(time.time())
        intervals = range(-window, window + 1)
        
        for i in intervals:
            t = (now // 30) + i
            msg = struct.pack(">Q", t)
            hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
            offset = hmac_hash[-1] & 0x0f
            binary = struct.unpack(">I", hmac_hash[offset:offset+4])[0] & 0x7fffffff
            calculated_code = str(binary % 1000000).zfill(6)
            if calculated_code == code:
                return True
    except Exception:
        return False
    return False

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> Optional[Token]:
        from sqlalchemy import select
        from app.core.security import generate_email_hash
        # Consulta unscoped porque no conocemos el tenant inicialmente, usando email_hash
        email_hash = generate_email_hash(email)
        query = select(Usuario).where(Usuario.email_hash == email_hash, Usuario.deleted_at.is_(None))
        result = await self.db.execute(query)
        user = result.scalars().first()

        if not user or not verify_password(password, user.hashed_password):
            return None

        # Si el usuario tiene 2FA habilitado, hacemos un gate emitiendo un token temporal de 2FA
        if user.two_factor_enabled:
            temp_token = create_access_token(
                {"sub": str(user.id), "type": "2fa_req", "tenant_id": str(user.tenant_id)},
                expires_minutes=5
            )
            return Token(access_token=temp_token, requires_2fa=True)

        return await self._generate_token_pair(user)

    async def _generate_token_pair(self, user: Usuario, familia_id: Optional[str] = None) -> Token:
        settings = Settings()
        
        # Access token
        payload = {
            "sub": str(user.id),
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "roles": [] # se resolverá en RBAC
        }
        access_token = create_access_token(payload, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Refresh token
        if not familia_id:
            familia_id = secrets.token_urlsafe(32)
            
        refresh_token_str = secrets.token_urlsafe(64)
        expira_el = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        rt = TokenRefresco(
            tenant_id=user.tenant_id,
            usuario_id=user.id,
            token=refresh_token_str,
            expira_el=expira_el,
            familia_id=familia_id
        )
        self.db.add(rt)
        await self.db.flush()
        
        return Token(access_token=access_token, refresh_token=refresh_token_str)

    async def refresh_token(self, refresh_token_str: str) -> Optional[Token]:
        from sqlalchemy import select
        # Consulta unscoped para encontrar el refresh token
        query = select(TokenRefresco).where(TokenRefresco.token == refresh_token_str)
        result = await self.db.execute(query)
        rt = result.scalars().first()

        if not rt:
            return None
            
        # ¿Está expirado?
        if rt.is_expired:
            await self.db.delete(rt)
            await self.db.flush()
            return None
            
        # Obtener usuario
        query_u = select(Usuario).where(Usuario.id == rt.usuario_id)
        result_u = await self.db.execute(query_u)
        user = result_u.scalars().first()
        
        if not user:
            return None

        # Rotar: Eliminar el viejo, generar uno nuevo con la misma familia
        familia_id = rt.familia_id
        await self.db.delete(rt)
        
        token_pair = await self._generate_token_pair(user, familia_id=familia_id)
        await self.db.commit()
        return token_pair

    async def verify_2fa(self, temp_token: str, totp_code: str) -> Optional[Token]:
        from sqlalchemy import select
        try:
            payload = decode_access_token(temp_token)
            if payload.get("type") != "2fa_req":
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
                
            query = select(Usuario).where(Usuario.id == UUID(user_id), Usuario.deleted_at.is_(None))
            result = await self.db.execute(query)
            user = result.scalars().first()
            
            if not user or not user.two_factor_secret:
                return None
                
            if not verify_totp(user.two_factor_secret, totp_code):
                return None
                
            token_pair = await self._generate_token_pair(user)
            await self.db.commit()
            return token_pair
        except Exception:
            return None

    async def enroll_2fa(self, user_id: UUID) -> Optional[Enroll2FAResponse]:
        from sqlalchemy import select
        query = select(Usuario).where(Usuario.id == user_id, Usuario.deleted_at.is_(None))
        result = await self.db.execute(query)
        user = result.scalars().first()
        if not user:
            return None
            
        secret = generate_totp_secret()
        # Generar URI estándar para Google Authenticator / Authy
        provisioning_uri = f"otpauth://totp/ActiveTrace:{user.email}?secret={secret}&issuer=ActiveTrace"
        
        user.two_factor_secret = secret
        # No habilitamos todavía hasta que verifique el primer código para evitar lockout
        user.two_factor_enabled = False
        
        await self.db.commit()
        return Enroll2FAResponse(secret=secret, provisioning_uri=provisioning_uri)

    async def enable_2fa(self, user_id: UUID, code: str) -> bool:
        from sqlalchemy import select
        query = select(Usuario).where(Usuario.id == user_id, Usuario.deleted_at.is_(None))
        result = await self.db.execute(query)
        user = result.scalars().first()
        if not user or not user.two_factor_secret:
            return False
            
        if verify_totp(user.two_factor_secret, code):
            user.two_factor_enabled = True
            await self.db.commit()
            return True
            
        return False

    async def forgot_password(self, email: str) -> Optional[str]:
        from sqlalchemy import select
        from app.core.security import generate_email_hash
        email_hash = generate_email_hash(email)
        query = select(Usuario).where(Usuario.email_hash == email_hash, Usuario.deleted_at.is_(None))
        result = await self.db.execute(query)
        user = result.scalars().first()
        if not user:
            return None
            
        # Token de recuperación de contraseña de corta duración (15 min)
        reset_token = create_access_token(
            {"sub": str(user.id), "type": "password_reset"},
            expires_minutes=15
        )
        # En producción se enviaría por email, aquí lo retornamos para poder testear y usarlo
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        from sqlalchemy import select
        try:
            payload = decode_access_token(token)
            if payload.get("type") != "password_reset":
                return False
                
            user_id = payload.get("sub")
            if not user_id:
                return False
                
            query = select(Usuario).where(Usuario.id == UUID(user_id), Usuario.deleted_at.is_(None))
            result = await self.db.execute(query)
            user = result.scalars().first()
            if not user:
                return False
                
            user.hashed_password = hash_password(new_password)
            await self.db.commit()
            return True
        except Exception:
            return False
        
    async def revoke_token(self, refresh_token_str: str, tenant_id: UUID) -> None:
        repo = TokenRefrescoRepository(TokenRefresco, self.db, tenant_id)
        rt = await repo.get_by_token(refresh_token_str)
        if rt:
            await repo.revoke_family(rt.familia_id)
            await self.db.commit()
