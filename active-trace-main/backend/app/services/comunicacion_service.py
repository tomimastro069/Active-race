from string import Template
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.exceptions import ServiceError
from app.core.config import Settings
from app.core.security import generate_email_hash
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.tenant import Tenant
from app.repositories.comunicacion import ComunicacionRepository
from app.schemas.comunicacion import (
    ComunicacionEnviarRequest,
    ComunicacionPreviewRequest,
    ComunicacionPreviewResponse,
)

# ---------------------------------------------------------------------------
# State machine definition
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[EstadoComunicacion, set[EstadoComunicacion]] = {
    EstadoComunicacion.PENDIENTE: {
        EstadoComunicacion.ENVIANDO,
        EstadoComunicacion.CANCELADO,
    },
    EstadoComunicacion.ENVIANDO: {
        EstadoComunicacion.ENVIADO,
        EstadoComunicacion.ERROR,
        EstadoComunicacion.PENDIENTE,  # retry after SMTP failure
    },
    EstadoComunicacion.ENVIADO: set(),   # terminal
    EstadoComunicacion.ERROR: {EstadoComunicacion.PENDIENTE},
    EstadoComunicacion.CANCELADO: set(),  # terminal
}


def _render(template_str: str, variables: dict) -> str:
    """Render a string template using safe_substitute (missing vars left as literals)."""
    return Template(template_str).safe_substitute(variables)


def _assert_transition(
    current: EstadoComunicacion,
    target: EstadoComunicacion,
) -> None:
    """Raise ServiceError if the transition current → target is not in VALID_TRANSITIONS."""
    if target not in VALID_TRANSITIONS[current]:
        raise ServiceError(
            f"Invalid state transition: {current.value} -> {target.value}"
        )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ComunicacionService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = ComunicacionRepository(db, tenant_id)

    # --- Pure helpers exposed on the class for convenience ---

    @staticmethod
    def _render(template_str: str, variables: dict) -> str:
        return _render(template_str, variables)

    @staticmethod
    def _assert_transition(
        current: EstadoComunicacion,
        target: EstadoComunicacion,
    ) -> None:
        return _assert_transition(current, target)

    # --- Synchronous endpoints ---

    def preview(self, request: ComunicacionPreviewRequest) -> ComunicacionPreviewResponse:
        """Render asunto + cuerpo templates. No DB interaction."""
        return ComunicacionPreviewResponse(
            asunto_renderizado=_render(request.asunto_template, request.variables),
            cuerpo_renderizado=_render(request.cuerpo_template, request.variables),
        )

    # --- Async endpoints ---

    async def encolar(
        self,
        request: ComunicacionEnviarRequest,
        current_user,
    ) -> list[Comunicacion]:
        """Enqueue one or more outbound communications.

        - enviado_por is taken from current_user.id (JWT) — never from body.
        - batch (>1 recipient) gets a shared lote_id.
        - aprobado defaults to True UNLESS tenant.aprobacion_comunicaciones_masivas
          AND this is a batch.
        """
        # Fetch tenant to check approval requirement.
        # Tenant is the root entity — its own tenant_id is NULL, so we bypass
        # the tenant-scoped BaseRepository and query directly.
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = result.scalars().first()
        if tenant is None:
            raise ServiceError("Tenant not found")

        es_batch = len(request.destinatarios) > 1
        lote_id = uuid4() if es_batch else None
        # Approval required only for batches when tenant has masivas=True
        aprobado_default = not (tenant.aprobacion_comunicaciones_masivas and es_batch)

        settings = Settings()
        creados: list[Comunicacion] = []

        for d in request.destinatarios:
            tvars = {
                "nombre": d.nombre,
                "materia": str(request.materia_id),
                "actividades_faltantes": d.actividades_faltantes,
            }
            row = Comunicacion(
                tenant_id=self.tenant_id,
                enviado_por=current_user.id,          # JWT-derived — never body
                materia_id=request.materia_id,
                destinatario=d.email,                  # encrypted by EncryptedString type
                destinatario_hash=generate_email_hash(d.email),
                asunto=_render(request.asunto_template, tvars),
                cuerpo=_render(request.cuerpo_template, tvars),
                estado=EstadoComunicacion.PENDIENTE,
                lote_id=lote_id,
                aprobado=aprobado_default,
                intentos=0,
                max_intentos=settings.MAX_INTENTOS,
            )
            await self.repo.create(row)
            creados.append(row)

        await self.db.commit()
        return creados

    async def aprobar_lote(self, lote_id: UUID, tenant_id: UUID) -> int:
        """Approve all PENDIENTE rows in a lote. Returns count of newly approved."""
        count = await self.repo.bulk_approve_lote(lote_id)
        await self.db.commit()
        return count

    async def aprobar_individual(self, comunicacion_id: UUID, tenant_id: UUID) -> Comunicacion:
        """Approve a single comunicacion. Idempotent: ENVIADO → no-op, returns row."""
        row = await self.repo.get_by_id(comunicacion_id)
        if row is None:
            raise ServiceError("Comunicacion not found")
        if row.estado == EstadoComunicacion.PENDIENTE:
            row.aprobado = True
            await self.db.commit()
        # For any other state (including ENVIADO), return row without error
        return row

    async def cancelar_lote(self, lote_id: UUID, tenant_id: UUID) -> int:
        """Cancel all PENDIENTE rows in a lote. Returns count of cancelled rows."""
        count = await self.repo.bulk_cancel_lote(lote_id)
        await self.db.commit()
        return count

    async def cancelar_individual(self, comunicacion_id: UUID, tenant_id: UUID) -> Comunicacion:
        """Cancel a single comunicacion.

        Raises ServiceError for any invalid transition (ENVIADO, CANCELADO, ENVIANDO).
        Maps to HTTP 409 in the router.
        """
        row = await self.repo.get_by_id(comunicacion_id)
        if row is None:
            raise ServiceError("Comunicacion not found")
        _assert_transition(row.estado, EstadoComunicacion.CANCELADO)
        row.estado = EstadoComunicacion.CANCELADO
        await self.db.commit()
        return row
