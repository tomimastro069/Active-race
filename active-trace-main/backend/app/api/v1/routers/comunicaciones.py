from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permission
from app.core.exceptions import ServiceError
from app.schemas.auth import CurrentUser
from app.schemas.comunicacion import (
    ComunicacionEnviarRequest,
    ComunicacionPreviewRequest,
    ComunicacionPreviewResponse,
    ComunicacionResponse,
    LoteResumenResponse,
)
from app.services.comunicacion_service import ComunicacionService

router = APIRouter(prefix="/comunicaciones", tags=["comunicaciones"])


@router.post("/preview", response_model=ComunicacionPreviewResponse)
async def preview_comunicacion(
    request: ComunicacionPreviewRequest,
    current_user: CurrentUser = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
) -> ComunicacionPreviewResponse:
    """Render asunto + cuerpo templates with variable substitution. No data is persisted."""
    svc = ComunicacionService(db, current_user.tenant_id)
    return svc.preview(request)


@router.post("/", response_model=list[ComunicacionResponse], status_code=status.HTTP_201_CREATED)
async def enqueue_comunicaciones(
    request: ComunicacionEnviarRequest,
    current_user: CurrentUser = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
) -> list[ComunicacionResponse]:
    """Enqueue one or more outbound communications. enviado_por is taken from JWT."""
    svc = ComunicacionService(db, current_user.tenant_id)
    rows = await svc.encolar(request, current_user)
    return rows


@router.get("/", response_model=list[ComunicacionResponse])
async def list_comunicaciones(
    current_user: CurrentUser = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
    estado: str | None = None,
    lote_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[ComunicacionResponse]:
    """List comunicaciones for the current tenant with optional filters."""
    from app.models.comunicacion import EstadoComunicacion
    from app.repositories.comunicacion import ComunicacionRepository

    repo = ComunicacionRepository(db, current_user.tenant_id)
    estado_enum = EstadoComunicacion(estado) if estado else None
    rows = await repo.list_filtered(
        estado=estado_enum,
        lote_id=lote_id,
        enviado_por=None,
        skip=skip,
        limit=limit,
    )
    return rows


@router.get("/lotes/{lote_id}", response_model=LoteResumenResponse)
async def lote_resumen(
    lote_id: UUID,
    current_user: CurrentUser = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
) -> LoteResumenResponse:
    """Return aggregate estado counts for a given lote."""
    from app.repositories.comunicacion import ComunicacionRepository

    repo = ComunicacionRepository(db, current_user.tenant_id)
    resumen = await repo.lote_resumen(lote_id)
    total = sum(resumen.values())
    return LoteResumenResponse(lote_id=lote_id, total=total, por_estado=resumen)


@router.post("/lotes/{lote_id}/aprobar", response_model=dict)
async def aprobar_lote(
    lote_id: UUID,
    current_user: CurrentUser = Depends(require_permission("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Approve all PENDIENTE rows in a lote, enabling dispatch."""
    svc = ComunicacionService(db, current_user.tenant_id)
    count = await svc.aprobar_lote(lote_id, current_user.tenant_id)
    return {"aprobados": count}


@router.post("/{comunicacion_id}/aprobar", response_model=ComunicacionResponse)
async def aprobar_individual(
    comunicacion_id: UUID,
    current_user: CurrentUser = Depends(require_permission("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
) -> ComunicacionResponse:
    """Approve a single comunicacion. Idempotent: ENVIADO rows return 200 with no change."""
    svc = ComunicacionService(db, current_user.tenant_id)
    row = await svc.aprobar_individual(comunicacion_id, current_user.tenant_id)
    return row


@router.post("/lotes/{lote_id}/cancelar", response_model=dict)
async def cancelar_lote(
    lote_id: UUID,
    current_user: CurrentUser = Depends(require_permission("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel all PENDIENTE rows in a lote."""
    svc = ComunicacionService(db, current_user.tenant_id)
    count = await svc.cancelar_lote(lote_id, current_user.tenant_id)
    return {"cancelados": count}


@router.post("/{comunicacion_id}/cancelar", response_model=ComunicacionResponse)
async def cancelar_individual(
    comunicacion_id: UUID,
    current_user: CurrentUser = Depends(require_permission("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
) -> ComunicacionResponse:
    """Cancel a single comunicacion.

    Returns HTTP 409 if the row is in a state that cannot be cancelled
    (ENVIADO, ENVIANDO, CANCELADO).
    """
    svc = ComunicacionService(db, current_user.tenant_id)
    try:
        row = await svc.cancelar_individual(comunicacion_id, current_user.tenant_id)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return row
