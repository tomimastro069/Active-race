import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from app.core.dependencies import get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.analisis import (
    AlumnoAtrasadoResponse,
    RankingResponse,
    ReporteRapidoResponse,
    NotasFinalesResponse,
    TPSinCorregirResponse,
    MonitorResponse
)
from app.services.analisis_service import AnalisisService

router = APIRouter(prefix="/analisis", tags=["analisis"])

@router.get("/atrasados", response_model=List[AlumnoAtrasadoResponse])
async def get_alumnos_atrasados(
    materia_id: UUID,
    cohorte_id: UUID,
    docente_id: Optional[UUID] = None,
    comision: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db)
):
    service = AnalisisService(db, current_user.tenant_id)
    try:
        return await service.obtener_alumnos_atrasados(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            current_user=current_user,
            docente_id=docente_id,
            comision=comision
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/ranking", response_model=List[RankingResponse])
async def get_ranking_aprobados(
    materia_id: UUID,
    cohorte_id: UUID,
    docente_id: Optional[UUID] = None,
    comision: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db)
):
    service = AnalisisService(db, current_user.tenant_id)
    try:
        return await service.obtener_ranking_aprobados(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            current_user=current_user,
            docente_id=docente_id,
            comision=comision
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/reporte-rapido", response_model=ReporteRapidoResponse)
async def get_reporte_rapido(
    materia_id: UUID,
    cohorte_id: UUID,
    docente_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db)
):
    service = AnalisisService(db, current_user.tenant_id)
    try:
        return await service.obtener_reporte_rapido(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            current_user=current_user,
            docente_id=docente_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/notas-finales", response_model=List[NotasFinalesResponse])
async def get_notas_finales(
    materia_id: UUID,
    cohorte_id: UUID,
    docente_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db)
):
    service = AnalisisService(db, current_user.tenant_id)
    try:
        return await service.obtener_notas_finales(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            current_user=current_user,
            docente_id=docente_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/tps-sin-corregir", response_model=List[TPSinCorregirResponse])
async def get_tps_sin_corregir(
    materia_id: UUID,
    cohorte_id: UUID,
    docente_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db)
):
    service = AnalisisService(db, current_user.tenant_id)
    try:
        return await service.obtener_tps_sin_corregir(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            current_user=current_user,
            docente_id=docente_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/tps-sin-corregir/export")
async def export_tps_sin_corregir(
    materia_id: UUID,
    cohorte_id: UUID,
    docente_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db)
):
    service = AnalisisService(db, current_user.tenant_id)
    try:
        tps = await service.obtener_tps_sin_corregir(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            current_user=current_user,
            docente_id=docente_id
        )
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID Alumno", "Nombre", "Apellido", "Actividad", "Fecha Importación"])
        for tp in tps:
            writer.writerow([
                str(tp["padron_id"]),
                tp["nombre"],
                tp["apellido"],
                tp["actividad"],
                tp["importado_at"].isoformat() if tp["importado_at"] else ""
            ])
            
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tps_sin_corregir.csv"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/monitor", response_model=List[MonitorResponse])
async def get_monitor_general(
    materia_id: UUID,
    cohorte_id: UUID,
    regional: Optional[str] = None,
    comision: Optional[str] = None,
    search: Optional[str] = None,
    estado_actividad: Optional[str] = None,
    desde_fecha: Optional[datetime] = None,
    hasta_fecha: Optional[datetime] = None,
    current_user: CurrentUser = Depends(require_permission("atrasados:ver")),
    db: AsyncSession = Depends(get_db)
):
    service = AnalisisService(db, current_user.tenant_id)
    try:
        return await service.obtener_monitor_general(
            current_user=current_user,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            regional=regional,
            comision=comision,
            search=search,
            estado_actividad=estado_actividad,
            desde_fecha=desde_fecha,
            hasta_fecha=hasta_fecha
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
