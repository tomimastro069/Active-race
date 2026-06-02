from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import Settings
from app.schemas.auth import CurrentUser
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """
    Decodifica el JWT (Stateless) y retorna el contexto de identidad (Golden Rule).
    No hit a DB para access token.
    """
    settings = Settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Nota: PyJWT o python-jose. Pyproject usa python-jose y PyJWT. 
        # Usaremos python-jose ya que es el standard de fastapi.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        email: str = payload.get("email", "unknown")
        
        if user_id is None or tenant_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    return CurrentUser(
        id=UUID(user_id),
        tenant_id=UUID(tenant_id),
        email=email,
        roles=payload.get("roles", [])
    )


# RESERVADO para C-04: get_tenant (resolución del tenant actual para multi-tenancy)
# async def get_tenant(...) -> Tenant:
#     pass

# RESERVADO para C-03: require_permission (autorización basada en roles/permisos)
# def require_permission(permission: str):
#     pass

