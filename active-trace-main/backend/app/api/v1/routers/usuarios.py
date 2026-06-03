from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.core.dependencies import get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.services.usuario import UsuarioService

router = APIRouter(prefix="/admin/usuarios", tags=["usuarios"])

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    payload: UsuarioCreate,
    current_user: CurrentUser = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = UsuarioService(db, current_user.tenant_id)
    try:
        user = await service.create_usuario(payload, actor_id=current_user.id)
        await db.commit()
        return service.to_response(user, mask_pii=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[UsuarioResponse])
async def list_usuarios(
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = UsuarioService(db, current_user.tenant_id)
    users = await service.list_usuarios(skip=skip, limit=limit)
    return [service.to_response(u, mask_pii=True) for u in users]

@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: UUID,
    current_user: CurrentUser = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = UsuarioService(db, current_user.tenant_id)
    user = await service.get_usuario(usuario_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no existe o pertenece a otro tenant."
        )
    return service.to_response(user, mask_pii=True)

@router.patch("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: UUID,
    payload: UsuarioUpdate,
    current_user: CurrentUser = Depends(require_permission("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = UsuarioService(db, current_user.tenant_id)
    try:
        user = await service.update_usuario(usuario_id, payload, actor_id=current_user.id)
        await db.commit()
        return service.to_response(user, mask_pii=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
