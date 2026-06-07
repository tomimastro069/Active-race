from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.usuario import UsuarioResponse
from app.services.usuario import UsuarioService
from app.core.security import generate_email_hash
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

router = APIRouter(prefix="/perfil", tags=["perfil"])

class PerfilUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    dni: Optional[str] = Field(None, max_length=50)
    cbu: Optional[str] = Field(None, max_length=50)
    alias_cbu: Optional[str] = Field(None, max_length=100)
    banco: Optional[str] = Field(None, max_length=100)
    regional: Optional[str] = Field(None, max_length=100)
    legajo: Optional[str] = Field(None, max_length=50)
    legajo_profesional: Optional[str] = Field(None, max_length=50)
    facturador: Optional[bool] = None
    modalidad_cobro: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = Field(None, description="Dirección de correo")
    cuil: Optional[str] = Field(None, description="CUIL (solo lectura)")

    model_config = ConfigDict(
        extra="forbid"
    )

@router.get("/", response_model=UsuarioResponse)
async def get_mi_perfil(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna el perfil del usuario autenticado.
    """
    service = UsuarioService(db, current_user.tenant_id)
    user = await service.get_usuario(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return service.to_response(user, mask_pii=True)

@router.patch("/", response_model=UsuarioResponse)
@router.put("/", response_model=UsuarioResponse)
async def update_mi_perfil(
    payload: PerfilUpdate,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza el perfil del usuario autenticado.
    El CUIL es de solo lectura y cualquier intento de modificarlo es rechazado.
    """
    if payload.cuil is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El campo CUIL es de solo lectura."
        )

    service = UsuarioService(db, current_user.tenant_id)
    user = await service.get_usuario(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    detalle_cambio = {}

    # Si se intenta cambiar el email
    if payload.email is not None and payload.email != user.email:
        email_hash = generate_email_hash(payload.email)
        # Verificar que no exista en el tenant
        existing = await service.repo.get_by_email_hash(email_hash)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado por otro usuario en este tenant."
            )
        detalle_cambio["email_antiguo"] = user.email
        detalle_cambio["email_nuevo"] = payload.email
        user.email = payload.email
        user.email_hash = email_hash

    # Mapear otros campos
    updatable_fields = [
        "nombre", "apellidos", "dni", "cbu", "alias_cbu",
        "banco", "regional", "legajo", "legajo_profesional", "facturador", "modalidad_cobro"
    ]

    for field in updatable_fields:
        val = getattr(payload, field)
        if val is not None:
            old_val = getattr(user, field)
            if val != old_val:
                if field in ["dni", "cbu", "alias_cbu"]:
                    detalle_cambio[field] = "MODIFICADO"
                else:
                    detalle_cambio[f"{field}_antiguo"] = old_val
                    detalle_cambio[f"{field}_nuevo"] = val
                setattr(user, field, val)

    if detalle_cambio:
        await service.repo.update(user)
        # Auditar cambios
        await service.audit_service.log_action(
            actor_id=current_user.id,
            accion="PERFIL_MODIFICAR",
            detalle={"id": str(user.id), **detalle_cambio}
        )
        await db.commit()

    return service.to_response(user, mask_pii=True)
