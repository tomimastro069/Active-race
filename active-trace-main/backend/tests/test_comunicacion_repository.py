"""
TDD tests for ComunicacionRepository.

Safety net: pre-existing failures are collection errors due to missing
prometheus_client module — NOT caused by this PR.
"""
import pytest
import uuid
from uuid import uuid4
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.materia import Materia
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.comunicacion import ComunicacionRepository


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
    u = Usuario(id=uuid4(), tenant_id=tenant_id, email=f"{uuid4().hex[:8]}@test.com", hashed_password="pwd")
    session.add(u)
    await session.flush()
    return u


async def _make_materia(session, tenant_id):
    m = Materia(id=uuid4(), tenant_id=tenant_id, codigo=f"MAT-{uuid4().hex[:6]}", nombre="Materia Test", estado="Activa")
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
    aprobado=False,
    lote_id=None,
):
    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant_id,
        enviado_por=enviado_por,
        materia_id=materia_id,
        destinatario="encrypted-placeholder",
        destinatario_hash="a" * 64,
        asunto="Test asunto",
        cuerpo="Test cuerpo",
        estado=estado,
        lote_id=lote_id,
        aprobado=aprobado,
        intentos=0,
        max_intentos=3,
    )
    session.add(c)
    await session.flush()
    return c


# ---------------------------------------------------------------------------
# T-09 RED: tests that MUST fail before ComunicacionRepository exists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_by_lote_returns_tenant_scoped_rows(db_session):
    """list_by_lote returns only rows belonging to the repo's tenant."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    c1 = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=lote_id)
    c2 = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=lote_id)

    # Different lote — same tenant
    other_lote = uuid4()
    await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=other_lote)

    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    results = await repo.list_by_lote(lote_id)

    ids = {r.id for r in results}
    assert c1.id in ids
    assert c2.id in ids
    assert len(results) == 2


@pytest.mark.asyncio
async def test_list_by_lote_empty_for_different_tenant(db_session):
    """list_by_lote returns empty for a different tenant's lote."""
    tenant_a = await _make_tenant(db_session)
    tenant_b = await _make_tenant(db_session)
    user_a = await _make_user(db_session, tenant_a.id)
    user_b = await _make_user(db_session, tenant_b.id)
    materia_a = await _make_materia(db_session, tenant_a.id)
    materia_b = await _make_materia(db_session, tenant_b.id)
    lote_id = uuid4()

    # Belongs to tenant_a
    await _make_comunicacion(db_session, tenant_a.id, user_a.id, materia_a.id, lote_id=lote_id)
    await db_session.commit()

    # repo scoped to tenant_b — must see nothing
    repo_b = ComunicacionRepository(db_session, tenant_b.id)
    results = await repo_b.list_by_lote(lote_id)

    assert results == []


@pytest.mark.asyncio
async def test_list_dispatchable_only_pendiente_aprobado(db_session):
    """list_dispatchable returns only PENDIENTE + aprobado=True records (cross-tenant)."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    # Should appear
    c_ok = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True
    )
    # Not aprobado
    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=False
    )
    # Wrong state
    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, aprobado=True
    )
    await db_session.commit()

    # Cross-tenant repo: use None as tenant_id placeholder but bypass _apply_tenant_scope
    repo = ComunicacionRepository.__new__(ComunicacionRepository)
    repo.model = Comunicacion
    repo.session = db_session
    repo.tenant_id = None  # cross-tenant — no scope applied

    results = await repo.list_dispatchable()
    ids = {r.id for r in results}
    assert c_ok.id in ids
    # Verify only aprobado=True AND PENDIENTE
    for r in results:
        assert r.aprobado is True
        assert r.estado == EstadoComunicacion.PENDIENTE


@pytest.mark.asyncio
async def test_list_dispatchable_excludes_unapproved(db_session):
    """list_dispatchable never returns unapproved entries."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=False
    )
    await db_session.commit()

    repo = ComunicacionRepository.__new__(ComunicacionRepository)
    repo.model = Comunicacion
    repo.session = db_session
    repo.tenant_id = None

    results = await repo.list_dispatchable()
    assert all(r.aprobado is True for r in results)


@pytest.mark.asyncio
async def test_bulk_approve_lote_only_pendiente(db_session):
    """bulk_approve_lote flips aprobado=True only on PENDIENTE rows."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    c_pend = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=False, lote_id=lote_id
    )
    c_env = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, aprobado=False, lote_id=lote_id
    )
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    count = await repo.bulk_approve_lote(lote_id)
    await db_session.commit()

    await db_session.refresh(c_pend)
    await db_session.refresh(c_env)

    assert count == 1
    assert c_pend.aprobado is True
    # ENVIADO row not touched
    assert c_env.aprobado is False


@pytest.mark.asyncio
async def test_bulk_cancel_lote_only_pendiente(db_session):
    """bulk_cancel_lote sets CANCELADO only on PENDIENTE rows."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    c_pend = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, lote_id=lote_id
    )
    c_env = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, lote_id=lote_id
    )
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    count = await repo.bulk_cancel_lote(lote_id)
    await db_session.commit()

    await db_session.refresh(c_pend)
    await db_session.refresh(c_env)

    assert count == 1
    assert c_pend.estado == EstadoComunicacion.CANCELADO
    assert c_env.estado == EstadoComunicacion.ENVIADO  # unchanged


@pytest.mark.asyncio
async def test_lote_resumen_counts_by_estado(db_session):
    """lote_resumen returns a dict with state counts for a lote."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, lote_id=lote_id
    )
    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, lote_id=lote_id
    )
    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, lote_id=lote_id
    )
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    resumen = await repo.lote_resumen(lote_id)

    assert resumen.get("Pendiente") == 1
    assert resumen.get("Enviado") == 2


# ---------------------------------------------------------------------------
# TRIANGULATE — additional cases per method
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_by_lote_returns_empty_for_unknown_lote(db_session):
    """list_by_lote returns empty list when lote_id doesn't exist."""
    tenant = await _make_tenant(db_session)
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    results = await repo.list_by_lote(uuid4())
    assert results == []


@pytest.mark.asyncio
async def test_bulk_approve_already_approved_not_double_counted(db_session):
    """bulk_approve_lote skips rows already aprobado=True (PENDIENTE)."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    # Already approved PENDIENTE — must NOT be counted as newly approved
    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=True, lote_id=lote_id
    )
    # Not approved PENDIENTE — must be counted
    c_new = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=False, lote_id=lote_id
    )
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    count = await repo.bulk_approve_lote(lote_id)
    await db_session.commit()

    await db_session.refresh(c_new)
    assert count == 1
    assert c_new.aprobado is True


@pytest.mark.asyncio
async def test_bulk_cancel_lote_returns_zero_when_none_pendiente(db_session):
    """bulk_cancel_lote returns 0 when no PENDIENTE rows in lote."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, lote_id=lote_id
    )
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    count = await repo.bulk_cancel_lote(lote_id)
    assert count == 0


@pytest.mark.asyncio
async def test_lote_resumen_empty_for_unknown_lote(db_session):
    """lote_resumen returns empty dict for unknown lote_id."""
    tenant = await _make_tenant(db_session)
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    resumen = await repo.lote_resumen(uuid4())
    assert resumen == {}


@pytest.mark.asyncio
async def test_list_filtered_by_estado(db_session):
    """list_filtered returns only rows matching the requested estado."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    await _make_comunicacion(db_session, tenant.id, user.id, materia.id, estado=EstadoComunicacion.PENDIENTE)
    c_env = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, estado=EstadoComunicacion.ENVIADO)
    await db_session.commit()

    repo = ComunicacionRepository(db_session, tenant.id)
    results = await repo.list_filtered(estado=EstadoComunicacion.ENVIADO)
    ids = {r.id for r in results}
    assert c_env.id in ids
    assert all(r.estado == EstadoComunicacion.ENVIADO for r in results)


@pytest.mark.asyncio
async def test_list_by_estado_sistema_cross_tenant(db_session):
    """list_by_estado_sistema returns rows from all tenants."""
    tenant_a = await _make_tenant(db_session)
    tenant_b = await _make_tenant(db_session)
    user_a = await _make_user(db_session, tenant_a.id)
    user_b = await _make_user(db_session, tenant_b.id)
    materia_a = await _make_materia(db_session, tenant_a.id)
    materia_b = await _make_materia(db_session, tenant_b.id)

    c_a = await _make_comunicacion(
        db_session, tenant_a.id, user_a.id, materia_a.id,
        estado=EstadoComunicacion.ENVIANDO
    )
    c_b = await _make_comunicacion(
        db_session, tenant_b.id, user_b.id, materia_b.id,
        estado=EstadoComunicacion.ENVIANDO
    )
    await db_session.commit()

    # Use __new__ to bypass _apply_tenant_scope (cross-tenant method)
    repo = ComunicacionRepository.__new__(ComunicacionRepository)
    repo.model = Comunicacion
    repo.session = db_session
    repo.tenant_id = None

    results = await repo.list_by_estado_sistema(EstadoComunicacion.ENVIANDO)
    ids = {r.id for r in results}
    assert c_a.id in ids
    assert c_b.id in ids
