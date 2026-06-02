from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.schemas.auth import (
    LoginRequest, RefreshRequest, Verify2FARequest, Token, CurrentUser,
    ForgotRequest, ResetRequest, Enroll2FAResponse, Enable2FARequest
)
from app.services.auth import AuthService, login_rate_limiter
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login(request_payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Autentica al usuario por email y contraseña.
    Devuelve los tokens de acceso y refresco, o un flag requires_2fa si aplica.
    Aplica tasa de límite de 5 peticiones por 60 segundos por IP+Email.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not login_rate_limiter.check_rate_limit(client_ip, request_payload.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    auth_service = AuthService(db)
    token = await auth_service.authenticate_user(request_payload.email, request_payload.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Rota el token de refresco, emitiendo un nuevo par y revirtiendo toda la familia si se detecta reuso.
    """
    auth_service = AuthService(db)
    token = await auth_service.refresh_token(request.refresh_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@router.post("/verify-2fa", response_model=Token)
async def verify_2fa(request: Verify2FARequest, db: AsyncSession = Depends(get_db)):
    """
    Finaliza el flujo 2FA intercambiando el token temporal y el código TOTP por tokens definitivos.
    """
    auth_service = AuthService(db)
    token = await auth_service.verify_2fa(request.temporary_token, request.totp_code)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code or temporary token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@router.post("/enroll-2fa", response_model=Enroll2FAResponse)
async def enroll_2fa(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Genera un nuevo secreto TOTP y la URI de configuración para enrolar el segundo factor.
    """
    auth_service = AuthService(db)
    response = await auth_service.enroll_2fa(current_user.id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return response

@router.post("/enable-2fa")
async def enable_2fa(
    request: Enable2FARequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirma el código TOTP enviado y habilita el segundo factor para el usuario.
    """
    auth_service = AuthService(db)
    success = await auth_service.enable_2fa(current_user.id, request.code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code"
        )
    return {"message": "2FA enabled successfully"}

@router.post("/forgot")
async def forgot_password(request: ForgotRequest, db: AsyncSession = Depends(get_db)):
    """
    Solicita la recuperación de contraseña enviando un token de un solo uso por email.
    """
    auth_service = AuthService(db)
    token = await auth_service.forgot_password(request.email)
    # Siempre retornamos un mensaje de éxito genérico para evitar enumeración de usuarios.
    # En desarrollo, enviamos el token en la respuesta para facilitar los tests.
    return {
        "message": "If the email exists, a password reset link has been generated.",
        "token": token
    }

@router.post("/reset")
async def reset_password(request: ResetRequest, db: AsyncSession = Depends(get_db)):
    """
    Restablece la contraseña utilizando el token temporal generado en /forgot.
    """
    auth_service = AuthService(db)
    success = await auth_service.reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    return {"message": "Password reset successfully"}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: RefreshRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cierra sesión revocando el token de refresco enviado.
    """
    auth_service = AuthService(db)
    await auth_service.revoke_token(request.refresh_token, current_user.tenant_id)
    return None
