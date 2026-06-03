from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import Settings
from app.schemas.auth import CurrentUser
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(request: Request = None, token: str = Depends(oauth2_scheme)) -> CurrentUser:
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
        email: str = payload.get("email", "unknown@example.com")
        impersonated_sub: str = payload.get("impersonated_sub")
        
        if user_id is None or tenant_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    active_user_id = impersonated_sub if impersonated_sub else user_id
    impersonated_by_id = user_id if impersonated_sub else None
    
    if request is not None:
        request.state.actor_id = UUID(user_id)
        request.state.impersonado_id = UUID(impersonated_sub) if impersonated_sub else None
        
    return CurrentUser(
        id=UUID(active_user_id),
        tenant_id=UUID(tenant_id),
        email=email,
        roles=payload.get("roles", []),
        impersonated_by_id=UUID(impersonated_by_id) if impersonated_by_id else None
    )


# RESERVADO para C-04: get_tenant (resolución del tenant actual para multi-tenancy)
# async def get_tenant(...) -> Tenant:
#     pass

def require_permission(permission_name: str):
    """
    Guard de seguridad que verifica si el usuario actual posee la capacidad requerida
    (o su variante contextual '_propio') resolviéndola en caliente de la base de datos.
    """
    async def dependency(
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> CurrentUser:
        from app.models.asignacion import Asignacion
        from app.repositories.asignacion import AsignacionRepository
        repo = AsignacionRepository(Asignacion, db, current_user.tenant_id)

        effective_permissions = await repo.get_effective_permissions(current_user.id)
        
        # Validación directa
        if permission_name in effective_permissions:
            return current_user
            
        # Validación contextual: si tiene '_propio', se aprueba preliminarmente 
        # y la lógica interna de los endpoints verificará la pertenencia del recurso.
        own_permission_name = f"{permission_name}_propio"
        if own_permission_name in effective_permissions:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return dependency
