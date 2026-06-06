from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.dependencies import get_db, require_permission, get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.tarea import TareaCreate, TareaUpdate, TareaResponse, ComentarioTareaCreate, ComentarioTareaResponse
from app.services.tarea_service import TareaService

router = APIRouter(tags=["Tareas"])

@router.get("/", response_model=List[TareaResponse])
async def list_tareas(
    skip: int = 0, limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("tareas:gestionar"))
):
    service = TareaService(db, current_user)
    return await service.get_tareas(skip=skip, limit=limit)

@router.post("/", response_model=TareaResponse, status_code=status.HTTP_201_CREATED)
async def create_tarea(
    tarea_in: TareaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("tareas:gestionar"))
):
    service = TareaService(db, current_user)
    try:
        tarea = await service.create_tarea(tarea_in)
        await db.commit()
        await db.refresh(tarea)
        return tarea
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/{tarea_id}", response_model=TareaResponse)
async def get_tarea(
    tarea_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("tareas:gestionar"))
):
    service = TareaService(db, current_user)
    try:
        return await service.get_tarea(tarea_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.patch("/{tarea_id}", response_model=TareaResponse)
async def update_tarea(
    tarea_id: UUID,
    tarea_in: TareaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("tareas:gestionar"))
):
    service = TareaService(db, current_user)
    try:
        tarea = await service.update_tarea(tarea_id, tarea_in)
        await db.commit()
        await db.refresh(tarea)
        return tarea
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/{tarea_id}/comentarios", response_model=List[ComentarioTareaResponse])
async def list_comentarios(
    tarea_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("tareas:gestionar"))
):
    service = TareaService(db, current_user)
    try:
        return await service.get_comentarios(tarea_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{tarea_id}/comentarios", response_model=ComentarioTareaResponse, status_code=status.HTTP_201_CREATED)
async def add_comentario(
    tarea_id: UUID,
    comentario_in: ComentarioTareaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("tareas:gestionar"))
):
    service = TareaService(db, current_user)
    try:
        comentario = await service.add_comentario(tarea_id, comentario_in)
        await db.commit()
        await db.refresh(comentario)
        return comentario
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
