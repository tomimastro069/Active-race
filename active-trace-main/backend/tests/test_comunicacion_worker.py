"""
TDD tests for the comunicacion worker.

SC-WRK-01: recover_stuck resets ENVIANDO → PENDIENTE
SC-WRK-02: dispatch_one on PENDIENTE → ENVIANDO → ENVIADO (success path)
SC-WRK-03: dispatch_one SMTP failure → retry (intentos < max_intentos → PENDIENTE)
SC-WRK-04: dispatch_one SMTP failure exhausted → ERROR (intentos == max_intentos)
SC-WRK-05: poll_once skips rows with aprobado=False
SC-AUD-01: dispatch_one success creates AuditLog entry

All SMTP calls are mocked via unittest.mock.AsyncMock.
NEVER assert on row.destinatario in tests (PII invariant).
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.materia import Materia


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


async def _make_tenant(session, aprobacion=False):
    t = Tenant(id=uuid4(), name=f"Tenant-{uuid4().hex[:8]}")
    t.aprobacion_comunicaciones_masivas = aprobacion
    session.add(t)
    await session.flush()
    return t


async def _make_user(session, tenant_id):
    u = Usuario(
        id=uuid4(), tenant_id=tenant_id,
        email=f"{uuid4().hex[:8]}@test.com", hashed_password="pwd"
    )
    session.add(u)
    await session.flush()
    return u


async def _make_materia(session, tenant_id):
    m = Materia(
        id=uuid4(), tenant_id=tenant_id,
        codigo=f"MAT-{uuid4().hex[:6]}", nombre="Test Materia", estado="Activa"
    )
    session.add(m)
    await session.flush()
    return m


async def _make_comunicacion(
    session,
    tenant_id,
    enviado_por,
    materia_id,
    *,
    estado=EstadoComunicacion.PENDIENTE,
    aprobado=True,
    intentos=0,
    max_intentos=3,
    lote_id=None,
):
    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant_id,
        enviado_por=enviado_por,
        materia_id=materia_id,
        destinatario="encrypted-placeholder",
        destinatario_hash="b" * 64,
        asunto="Test asunto",
        cuerpo="Test cuerpo",
        estado=estado,
        lote_id=lote_id,
        aprobado=aprobado,
        intentos=intentos,
        max_intentos=max_intentos,
    )
    session.add(c)
    await session.flush()
    return c


# ---------------------------------------------------------------------------
# SC-WRK-01: recover_stuck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recover_stuck_resets_enviando_to_pendiente(db_session):
    """SC-WRK-01: rows in ENVIANDO state get reset to PENDIENTE on startup."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c1 = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIANDO
    )
    c2 = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIANDO
    )
    # PENDIENTE — must NOT be touched
    c3 = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE
    )
    await db_session.commit()

    from app.workers.main import recover_stuck
    count = await recover_stuck(db_session)

    await db_session.refresh(c1)
    await db_session.refresh(c2)
    await db_session.refresh(c3)

    assert count == 2
    assert c1.estado == EstadoComunicacion.PENDIENTE
    assert c2.estado == EstadoComunicacion.PENDIENTE
    assert c3.estado == EstadoComunicacion.PENDIENTE  # unchanged


@pytest.mark.asyncio
async def test_recover_stuck_returns_zero_when_none_stuck(db_session):
    """recover_stuck returns 0 when no ENVIANDO rows exist."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE
    )
    await db_session.commit()

    from app.workers.main import recover_stuck
    count = await recover_stuck(db_session)
    assert count == 0


# ---------------------------------------------------------------------------
# SC-WRK-02: dispatch_one — success path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_one_success_transitions_to_enviado(db_session):
    """SC-WRK-02: PENDIENTE + aprobado=True → ENVIANDO then ENVIADO after SMTP."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True
    )
    await db_session.commit()

    settings = MagicMock()
    settings.SMTP_HOST = "localhost"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = ""
    settings.SMTP_PASSWORD = ""
    settings.SMTP_FROM = "test@example.com"

    with patch("app.workers.main.send_email", new_callable=AsyncMock) as mock_smtp:
        from app.workers.main import dispatch_one
        await dispatch_one(c, db_session, settings)

    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.ENVIADO
    assert c.enviado_at is not None
    mock_smtp.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_one_sets_enviado_at(db_session):
    """dispatch_one sets enviado_at to a datetime on success."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True
    )
    await db_session.commit()

    settings = MagicMock()
    settings.SMTP_HOST = "localhost"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = ""
    settings.SMTP_PASSWORD = ""
    settings.SMTP_FROM = "test@example.com"

    with patch("app.workers.main.send_email", new_callable=AsyncMock):
        from app.workers.main import dispatch_one
        await dispatch_one(c, db_session, settings)

    await db_session.refresh(c)
    assert isinstance(c.enviado_at, datetime)


# ---------------------------------------------------------------------------
# SC-WRK-03: dispatch_one — SMTP failure + retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_one_smtp_failure_increments_intentos_to_pendiente(db_session):
    """SC-WRK-03: SMTP failure with intentos < max_intentos → intentos++ + PENDIENTE."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True,
        intentos=0, max_intentos=3
    )
    await db_session.commit()

    settings = MagicMock()

    with patch(
        "app.workers.main.send_email",
        new_callable=AsyncMock,
        side_effect=Exception("SMTP timeout"),
    ):
        from app.workers.main import dispatch_one
        await dispatch_one(c, db_session, settings)

    await db_session.refresh(c)
    assert c.intentos == 1
    assert c.estado == EstadoComunicacion.PENDIENTE


# ---------------------------------------------------------------------------
# SC-WRK-04: dispatch_one — exhausted retries → ERROR
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_one_smtp_failure_exhausted_transitions_to_error(db_session):
    """SC-WRK-04: SMTP failure with intentos == max_intentos - 1 → ERROR terminal."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True,
        intentos=2, max_intentos=3
    )
    await db_session.commit()

    settings = MagicMock()

    with patch(
        "app.workers.main.send_email",
        new_callable=AsyncMock,
        side_effect=Exception("SMTP error"),
    ):
        from app.workers.main import dispatch_one
        await dispatch_one(c, db_session, settings)

    await db_session.refresh(c)
    assert c.intentos == 3
    assert c.estado == EstadoComunicacion.ERROR


# ---------------------------------------------------------------------------
# SC-WRK-05: poll_once skips unapproved rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_once_skips_unapproved_rows(db_session):
    """SC-WRK-05: poll_once never dispatches rows with aprobado=False."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    # unapproved
    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=False
    )
    await db_session.commit()

    settings = MagicMock()

    with patch("app.workers.main.send_email", new_callable=AsyncMock) as mock_smtp:
        from app.workers.main import poll_once
        await poll_once(db_session, settings)

    mock_smtp.assert_not_called()


@pytest.mark.asyncio
async def test_poll_once_dispatches_approved_rows(db_session):
    """poll_once calls send_email for PENDIENTE + aprobado=True rows."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True
    )
    await db_session.commit()

    settings = MagicMock()

    with patch("app.workers.main.send_email", new_callable=AsyncMock) as mock_smtp:
        from app.workers.main import poll_once
        await poll_once(db_session, settings)

    mock_smtp.assert_called_once()


# ---------------------------------------------------------------------------
# SC-AUD-01: dispatch_one success creates AuditLog
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_one_success_creates_audit_log(db_session):
    """SC-AUD-01: successful dispatch creates AuditLog with COMUNICACION_ENVIAR."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True
    )
    await db_session.commit()

    settings = MagicMock()

    with patch("app.workers.main.send_email", new_callable=AsyncMock):
        from app.workers.main import dispatch_one
        await dispatch_one(c, db_session, settings)

    from sqlalchemy import select
    from app.models.audit_log import AuditLog
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.accion == "COMUNICACION_ENVIAR")
    )
    audit_rows = result.scalars().all()
    assert len(audit_rows) >= 1
    assert audit_rows[0].actor_id == user.id


@pytest.mark.asyncio
async def test_dispatch_one_failure_no_audit_log(db_session):
    """SC-AUD-02: failed dispatch must NOT create AuditLog."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True
    )
    await db_session.commit()

    settings = MagicMock()

    with patch(
        "app.workers.main.send_email",
        new_callable=AsyncMock,
        side_effect=Exception("fail"),
    ):
        from app.workers.main import dispatch_one
        await dispatch_one(c, db_session, settings)

    from sqlalchemy import select
    from app.models.audit_log import AuditLog
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.accion == "COMUNICACION_ENVIAR")
    )
    audit_rows = result.scalars().all()
    assert len(audit_rows) == 0
