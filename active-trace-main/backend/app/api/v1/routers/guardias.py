from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional

from app.core.dependencies import get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.guardia import GuardiaCreate, GuardiaResponse
from app.services.guardia_service import GuardiaService
from app.models.guardia import Guardia
from app.models.asignacion import Asignacion

router = APIRouter(prefix="/guardias", tags=["guardias"])

@router.post("/", response_model=GuardiaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_guardia(
    payload: GuardiaCreate,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = GuardiaService(db, current_user.tenant_id)
    try:
        guardia = await service.registrar_guardia(payload, actor_id=current_user.id)
        await db.commit()
        return guardia
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[GuardiaResponse])
async def list_guardias(
    materia_id: Optional[UUID] = None,
    cohorte_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = GuardiaService(db, current_user.tenant_id)
    query = select(Guardia)
    if materia_id:
        query = query.where(Guardia.materia_id == materia_id)
    if cohorte_id:
        query = query.join(Asignacion, Guardia.asignacion_id == Asignacion.id).where(
            Asignacion.cohorte_id == cohorte_id
        )
    query = service.repo._apply_tenant_scope(query)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{guardia_id}/aprobar", response_model=GuardiaResponse)
async def aprobar_guardia(
    guardia_id: UUID,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = GuardiaService(db, current_user.tenant_id)
    try:
        guardia = await service.aprobar_guardia(guardia_id, actor_id=current_user.id)
        await db.commit()
        return guardia
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
