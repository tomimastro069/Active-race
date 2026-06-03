from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.core.dependencies import get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.asignacion import AsignacionCreate, AsignacionUpdate, AsignacionResponse
from app.services.asignacion import AsignacionService

router = APIRouter(prefix="/asignaciones", tags=["asignaciones"])

@router.post("/", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AsignacionCreate,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = AsignacionService(db, current_user.tenant_id)
    try:
        asig = await service.create_assignment(payload, actor_id=current_user.id)
        await db.commit()
        return asig
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[AsignacionResponse])
async def list_assignments(
    usuario_id: Optional[UUID] = None,
    rol_id: Optional[UUID] = None,
    materia_id: Optional[UUID] = None,
    carrera_id: Optional[UUID] = None,
    cohorte_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = AsignacionService(db, current_user.tenant_id)
    return await service.list_assignments(
        usuario_id=usuario_id,
        rol_id=rol_id,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        skip=skip,
        limit=limit
    )

@router.get("/{asig_id}", response_model=AsignacionResponse)
async def get_assignment(
    asig_id: UUID,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = AsignacionService(db, current_user.tenant_id)
    asig = await service.get_assignment(asig_id)
    if not asig:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La asignación no existe o pertenece a otro tenant."
        )
    return asig

@router.patch("/{asig_id}", response_model=AsignacionResponse)
async def update_assignment(
    asig_id: UUID,
    payload: AsignacionUpdate,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = AsignacionService(db, current_user.tenant_id)
    try:
        asig = await service.update_assignment(asig_id, payload, actor_id=current_user.id)
        await db.commit()
        return asig
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{asig_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    asig_id: UUID,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = AsignacionService(db, current_user.tenant_id)
    try:
        await service.delete_assignment(asig_id, actor_id=current_user.id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
