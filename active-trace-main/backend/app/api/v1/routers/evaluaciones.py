from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from app.core.dependencies import get_db, require_permission, get_current_user
from app.schemas.auth import CurrentUser
from app.models.evaluacion import Evaluacion, EvaluacionTipoEnum
from app.schemas.evaluacion import (
    ReservaCreate, ReservaResponse, EvaluacionResumenResponse,
    ConvocadosImport, ConvocadosImportResponse, AgendaReservaResponse,
    ResultadoCreate, ResultadoResponse,
)
from app.crud.crud_evaluacion import CRUDEvaluacion
from pydantic import BaseModel, ConfigDict

router = APIRouter(tags=["Evaluaciones"])

class EvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    materia_id: UUID
    cohorte_id: UUID
    tipo: EvaluacionTipoEnum
    instancia: str
    titulo: Optional[str] = None
    fecha: Optional[date] = None
    dias_disponibles: int = 1
    cupos_totales: int = 10

class EvaluacionResponse(BaseModel):
    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: EvaluacionTipoEnum
    instancia: str
    titulo: Optional[str] = None
    fecha: Optional[date] = None
    dias_disponibles: int
    cupos_totales: int

    model_config = ConfigDict(from_attributes=True)

@router.post("/admin/evaluaciones/", response_model=EvaluacionResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluacion(
    eval_in: EvaluacionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar"))
):
    evaluacion = Evaluacion(
        tenant_id=current_user.tenant_id,
        materia_id=eval_in.materia_id,
        cohorte_id=eval_in.cohorte_id,
        tipo=eval_in.tipo,
        instancia=eval_in.instancia,
        titulo=eval_in.titulo,
        fecha=eval_in.fecha,
        dias_disponibles=eval_in.dias_disponibles,
        cupos_totales=eval_in.cupos_totales
    )
    db.add(evaluacion)
    await db.commit()
    await db.refresh(evaluacion)
    return evaluacion

@router.get("/admin/evaluaciones/", response_model=List[EvaluacionResumenResponse])
async def listar_evaluaciones(
    tipo: Optional[EvaluacionTipoEnum] = None,
    materia_id: Optional[UUID] = None,
    cohorte_id: Optional[UUID] = None,
    orden: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
):
    """Tabla lineal / calendario de evaluaciones con contadores (HU-24, HU-31).

    ``orden=fecha`` devuelve las instancias ordenadas por fecha académica (calendario).
    """
    crud = CRUDEvaluacion(db, current_user.tenant_id)
    return await crud.listar_evaluaciones(
        tipo=tipo, materia_id=materia_id, cohorte_id=cohorte_id,
        orden_por_fecha=(orden == "fecha"),
    )


@router.get("/admin/evaluaciones/cronograma/{materia_id}", response_class=HTMLResponse)
async def cronograma_evaluaciones(
    materia_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
):
    """Genera el cronograma de evaluaciones embebible en el LMS (HU-24)."""
    crud = CRUDEvaluacion(db, current_user.tenant_id)
    items = await crud.listar_evaluaciones(materia_id=materia_id, orden_por_fecha=True)

    html = ['<div class="cronograma-evaluaciones">', '  <h3>Cronograma de Evaluaciones</h3>']
    if not items:
        html.append('  <p>No hay evaluaciones programadas.</p>')
    else:
        html.append('  <ul>')
        for ev in items:
            fecha_str = ev["fecha"].strftime("%d/%m/%Y") if ev["fecha"] else "Fecha a confirmar"
            titulo = ev["titulo"] or ev["instancia"]
            html.append(f'    <li><strong>{ev["tipo"].value} {ev["instancia"]}</strong> — {titulo}: {fecha_str}</li>')
        html.append('  </ul>')
    html.append('</div>')
    return "\n".join(html)

@router.post(
    "/admin/evaluaciones/{evaluacion_id}/convocados",
    response_model=ConvocadosImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def importar_convocados(
    evaluacion_id: UUID,
    payload: ConvocadosImport,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
):
    """Importa el padrón de alumnos elegibles de un coloquio (HU-30)."""
    crud = CRUDEvaluacion(db, current_user.tenant_id)
    try:
        resultado = await crud.importar_convocados(evaluacion_id, payload.alumno_ids)
        await db.commit()
        return resultado
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/reservas/agenda", response_model=List[AgendaReservaResponse])
async def obtener_agenda(
    materia_id: Optional[UUID] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
):
    """Agenda consolidada de reservas activas con filtros (HU-32)."""
    crud = CRUDEvaluacion(db, current_user.tenant_id)
    return await crud.obtener_agenda(materia_id=materia_id, desde=desde, hasta=hasta, search=search)

@router.post(
    "/admin/evaluaciones/{evaluacion_id}/resultados",
    response_model=ResultadoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def cargar_resultado(
    evaluacion_id: UUID,
    payload: ResultadoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
):
    """Carga la nota final de un alumno en una instancia (HU-33)."""
    crud = CRUDEvaluacion(db, current_user.tenant_id)
    try:
        resultado = await crud.cargar_resultado(evaluacion_id, payload.alumno_id, payload.nota_final)
        await db.commit()
        await db.refresh(resultado)
        return ResultadoResponse.model_validate(resultado)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/admin/evaluaciones/registro", response_model=List[ResultadoResponse])
async def obtener_registro_academico(
    evaluacion_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
):
    """Registro académico consolidado de notas finales de coloquios (HU-33)."""
    crud = CRUDEvaluacion(db, current_user.tenant_id)
    return await crud.obtener_registro_academico(evaluacion_id=evaluacion_id)

@router.post("/reservas/evaluaciones/", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
async def reservar_evaluacion(
    reserva_in: ReservaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    # Only ALUMNO or self reservation
    if str(current_user.id) != str(reserva_in.alumno_id) and "ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="No puedes reservar para otro alumno")
    
    crud = CRUDEvaluacion(db, current_user.tenant_id)
    try:
        reserva = await crud.reservar_evaluacion(reserva_in)
        await db.commit()
        await db.refresh(reserva)
        return reserva
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
