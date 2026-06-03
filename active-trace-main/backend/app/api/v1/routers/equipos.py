from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.core.dependencies import get_db, require_permission, get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.asignacion import AsignacionResponse, AsignacionMasivaCreate, EquipoClonarRequest, AsignacionVigenciaUpdate
from app.services.equipos import EquiposService

router = APIRouter(prefix="/equipos", tags=["equipos"])

# 3.6 GET /api/v1/equipos/mis-equipos
@router.get("/mis-equipos", response_model=List[AsignacionResponse])
async def obtener_mis_equipos(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EquiposService(db, current_user.tenant_id)
    return await service.obtener_mis_equipos(current_user.id)

# Router con guard a nivel router
admin_router = APIRouter(dependencies=[Depends(require_permission("equipos:asignar"))])

# 3.2 POST /api/v1/equipos/masiva
@admin_router.post("/masiva", response_model=List[AsignacionResponse], status_code=status.HTTP_201_CREATED)
async def asignacion_masiva(
    payload: AsignacionMasivaCreate,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = EquiposService(db, current_user.tenant_id)
    try:
        assignments = await service.asignacion_masiva(payload, actor_id=current_user.id)
        await db.commit()
        return assignments
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 3.3 POST /api/v1/equipos/clonar
@admin_router.post("/clonar", response_model=List[AsignacionResponse], status_code=status.HTTP_201_CREATED)
async def clonar_equipo(
    payload: EquipoClonarRequest,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = EquiposService(db, current_user.tenant_id)
    try:
        assignments = await service.clonar_equipo(payload, actor_id=current_user.id)
        await db.commit()
        return assignments
    except ValueError as e:
        if "destino ya tiene asignaciones activas" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 3.4 PATCH /api/v1/equipos/vigencia
@admin_router.patch("/vigencia", response_model=List[AsignacionResponse])
async def modificar_vigencia_masiva(
    payload: AsignacionVigenciaUpdate,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = EquiposService(db, current_user.tenant_id)
    try:
        assignments = await service.modificar_vigencia_masiva(payload, actor_id=current_user.id)
        await db.commit()
        return assignments
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 3.5 GET /api/v1/equipos/exportar
@admin_router.get("/exportar")
async def exportar_equipo(
    materia_id: Optional[UUID] = None,
    carrera_id: Optional[UUID] = None,
    cohorte_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_permission("equipos:asignar")),
    db: AsyncSession = Depends(get_db)
):
    service = EquiposService(db, current_user.tenant_id)
    try:
        csv_data = await service.exportar_equipo(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id
        )
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=equipo_docente.csv"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

router.include_router(admin_router)
