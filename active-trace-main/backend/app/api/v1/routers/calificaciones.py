from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.core.dependencies import get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.calificacion import (
    CalificacionPreviewResponse,
    CalificacionImportResponse,
    CalificacionVaciarRequest,
    UmbralConfigPayload
)
from app.schemas.umbral import UmbralMateriaResponse
from app.services.calificacion_service import CalificacionService

router = APIRouter(prefix="/calificaciones", tags=["calificaciones"])

@router.post("/preview-csv", response_model=CalificacionPreviewResponse)
async def preview_calificaciones_csv(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db)
):
    service = CalificacionService(db, current_user.tenant_id)
    try:
        content = await file.read()
        file_str = content.decode('utf-8')
        return await service.preview_csv(file_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar la previsualización: {str(e)}"
        )

@router.post("/import-csv", response_model=CalificacionImportResponse, status_code=status.HTTP_201_CREATED)
async def import_calificaciones_csv(
    materia_id: UUID = Form(...),
    cohorte_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db)
):
    service = CalificacionService(db, current_user.tenant_id)
    try:
        content = await file.read()
        file_str = content.decode('utf-8')
        res = await service.importar_calificaciones_csv(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            docente_id=current_user.id,
            file_content=file_str
        )
        await db.commit()
        return res
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/import-completion-csv", response_model=CalificacionImportResponse, status_code=status.HTTP_201_CREATED)
async def import_finalizaciones_csv(
    materia_id: UUID = Form(...),
    cohorte_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db)
):
    service = CalificacionService(db, current_user.tenant_id)
    try:
        content = await file.read()
        file_str = content.decode('utf-8')
        res = await service.importar_finalizaciones_csv(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            docente_id=current_user.id,
            file_content=file_str
        )
        await db.commit()
        return res
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/vaciar")
async def vaciar_calificaciones(
    payload: CalificacionVaciarRequest,
    current_user: CurrentUser = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db)
):
    service = CalificacionService(db, current_user.tenant_id)
    try:
        deleted_count = await service.vaciar_calificaciones(
            materia_id=payload.materia_id,
            docente_id=current_user.id
        )
        await db.commit()
        return {
            "status": "success",
            "detail": f"Se eliminaron {deleted_count} calificaciones correctamente."
        }
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/umbral", response_model=UmbralMateriaResponse)
async def configurar_umbral(
    payload: UmbralConfigPayload,
    current_user: CurrentUser = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db)
):
    service = CalificacionService(db, current_user.tenant_id)
    try:
        umbral = await service.configurar_umbral(
            docente_id=current_user.id,
            materia_id=payload.materia_id,
            umbral_pct=payload.umbral_pct,
            valores_aprobatorios=payload.valores_aprobatorios
        )
        await db.commit()
        return umbral
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/umbral", response_model=Optional[UmbralMateriaResponse])
async def get_umbral(
    materia_id: UUID,
    current_user: CurrentUser = Depends(require_permission("calificaciones:importar")),
    db: AsyncSession = Depends(get_db)
):
    service = CalificacionService(db, current_user.tenant_id)
    return await service.get_umbral(
        docente_id=current_user.id,
        materia_id=materia_id
    )
