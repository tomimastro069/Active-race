"""
Async worker for dispatching outbound comunicaciones.

Functions are individually testable — the `while True` loop lives only in
`run_worker()` which is NOT called during tests.

Security invariant: `dispatch_one` NEVER logs `row.destinatario` (AES-256 PII).
Only `row.id`, `row.destinatario_hash`, and `row.estado.value` appear in logs.
"""

import asyncio
import logging
from datetime import datetime, timezone
from email.message import EmailMessage

import aiosmtplib

from app.core.config import Settings
from app.core.database import SessionLocal
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.comunicacion import ComunicacionRepository
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


async def send_email(settings: Settings, to: str, subject: str, body: str) -> None:
    """Send a single email via SMTP. Extracted to allow clean mocking in tests."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg.set_content(body)
    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=settings.SMTP_PORT == 587,
    )


async def recover_stuck(session) -> int:
    """SYSTEM-LEVEL crash recovery: reset ENVIANDO rows to PENDIENTE.

    Called once at worker startup. Returns count of recovered rows.
    No tenant scope — operates across all tenants.
    """
    repo = ComunicacionRepository(session, tenant_id=None)  # cross-tenant
    stuck = await repo.list_by_estado_sistema(EstadoComunicacion.ENVIANDO)
    for row in stuck:
        row.estado = EstadoComunicacion.PENDIENTE
    if stuck:
        await session.commit()
    return len(stuck)


async def dispatch_one(row: Comunicacion, session, settings: Settings) -> None:
    """Dispatch a single comunicacion via SMTP.

    State machine:
      PENDIENTE → ENVIANDO (committed before SMTP call)
      ENVIANDO  → ENVIADO  (on success) + AuditLog
      ENVIANDO  → PENDIENTE (if intentos < max_intentos, retry)
      ENVIANDO  → ERROR     (if intentos >= max_intentos)

    NEVER logs row.destinatario. Only id, destinatario_hash, estado are logged.
    """
    row.estado = EstadoComunicacion.ENVIANDO
    await session.commit()

    try:
        await send_email(settings, row.destinatario, row.asunto, row.cuerpo)
    except Exception as exc:
        row.intentos += 1
        if row.intentos < row.max_intentos:
            row.estado = EstadoComunicacion.PENDIENTE
        else:
            row.estado = EstadoComunicacion.ERROR
        await session.commit()
        # SECURITY: NEVER log row.destinatario — only safe identifiers
        logger.warning(
            "dispatch failed id=%s hash=%s intentos=%s estado=%s err=%s",
            row.id,
            row.destinatario_hash,
            row.intentos,
            row.estado.value,
            type(exc).__name__,
        )
        return

    row.estado = EstadoComunicacion.ENVIADO
    row.enviado_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()

    await AuditService(session, row.tenant_id).log_action(
        actor_id=row.enviado_por,
        accion="COMUNICACION_ENVIAR",
        materia_id=row.materia_id,
        filas_afectadas=1,
    )
    await session.commit()


async def poll_once(session, settings: Settings) -> None:
    """Run a single worker poll cycle: dispatch all PENDIENTE + aprobado=True rows.

    SYSTEM-LEVEL: cross-tenant, no JWT context.
    """
    repo = ComunicacionRepository(session, tenant_id=None)  # cross-tenant
    rows = await repo.list_dispatchable()
    for row in rows:
        await dispatch_one(row, session, settings)


async def run_worker() -> None:
    """Worker entrypoint with crash recovery and polling loop.

    This function is the production entrypoint. It is NOT directly tested
    (contains `while True`). Test `recover_stuck`, `poll_once`, and
    `dispatch_one` individually.
    """
    settings = Settings()

    async with SessionLocal() as session:
        n = await recover_stuck(session)
        logger.info("crash recovery: requeued %d ENVIANDO rows", n)

    while True:
        try:
            async with SessionLocal() as session:
                await poll_once(session, settings)
        except Exception as exc:
            logger.error("poll_once error: %s", type(exc).__name__, exc_info=True)

        await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
