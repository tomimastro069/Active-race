"""
TDD tests for ComunicacionService — state machine, helpers, preview, encolar,
aprobacion, and cancelacion.

All DB-touching tests use a real PostgreSQL test DB via db_session fixture.
Unit tests (state machine + render) are purely synchronous with no DB.
"""

import pytest
from string import Template
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ServiceError
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.materia import Materia
from app.schemas.comunicacion import (
    ComunicacionPreviewRequest,
    ComunicacionResponse,
)
from app.services.comunicacion_service import (
    VALID_TRANSITIONS,
    ComunicacionService,
    _assert_transition,
    _render,
)


# ---------------------------------------------------------------------------
# T-11: State machine + pure helpers (SC-SM-01, SC-SM-02, SC-SM-03, SC-PRV-01,
#       SC-PRV-02, SC-PRV-03) — 100% synchronous, no DB
# ---------------------------------------------------------------------------


class TestValidTransitions:
    """SC-SM-01: Valid transitions are accepted without raising."""

    def test_pendiente_to_enviando(self):
        _assert_transition(EstadoComunicacion.PENDIENTE, EstadoComunicacion.ENVIANDO)

    def test_pendiente_to_cancelado(self):
        _assert_transition(EstadoComunicacion.PENDIENTE, EstadoComunicacion.CANCELADO)

    def test_enviando_to_enviado(self):
        _assert_transition(EstadoComunicacion.ENVIANDO, EstadoComunicacion.ENVIADO)

    def test_enviando_to_error(self):
        _assert_transition(EstadoComunicacion.ENVIANDO, EstadoComunicacion.ERROR)

    def test_enviando_to_pendiente(self):
        _assert_transition(EstadoComunicacion.ENVIANDO, EstadoComunicacion.PENDIENTE)

    def test_error_to_pendiente(self):
        _assert_transition(EstadoComunicacion.ERROR, EstadoComunicacion.PENDIENTE)


class TestInvalidTransitions:
    """SC-SM-02 + SC-SM-03: Terminal states raise ServiceError."""

    def test_enviado_to_any_raises(self):
        with pytest.raises(ServiceError):
            _assert_transition(EstadoComunicacion.ENVIADO, EstadoComunicacion.PENDIENTE)

    def test_cancelado_to_any_raises(self):
        with pytest.raises(ServiceError):
            _assert_transition(EstadoComunicacion.CANCELADO, EstadoComunicacion.PENDIENTE)

    def test_pendiente_to_enviado_raises(self):
        with pytest.raises(ServiceError):
            _assert_transition(EstadoComunicacion.PENDIENTE, EstadoComunicacion.ENVIADO)

    def test_error_to_enviado_raises(self):
        with pytest.raises(ServiceError):
            _assert_transition(EstadoComunicacion.ERROR, EstadoComunicacion.ENVIADO)


class TestRender:
    """SC-PRV-01, SC-PRV-02, SC-PRV-03: Template rendering with safe_substitute."""

    def test_variables_substituted(self):
        result = _render("Hola $nombre, tenés $actividades_faltantes pendientes", {
            "nombre": "Ana",
            "actividades_faltantes": "TP1, TP2",
        })
        assert result == "Hola Ana, tenés TP1, TP2 pendientes"

    def test_missing_variable_left_as_literal(self):
        result = _render("Materia: $materia", {})
        assert result == "Materia: $materia"

    def test_empty_variables_dict(self):
        result = _render("Hola $nombre", {})
        assert "$nombre" in result

    def test_extra_variables_not_in_template(self):
        result = _render("Hola $nombre", {"nombre": "Carlos", "extra": "ignored"})
        assert result == "Hola Carlos"


# ---------------------------------------------------------------------------
# T-10 (schema invariant): SC-ENC-01 Case A — destinatario NOT in model_fields
# ---------------------------------------------------------------------------


class TestComunicacionResponseSchema:
    """SC-ENC-01: ComunicacionResponse MUST NOT expose destinatario field."""

    def test_destinatario_not_in_model_fields(self):
        assert "destinatario" not in ComunicacionResponse.model_fields

    def test_destinatario_hash_is_present(self):
        assert "destinatario_hash" in ComunicacionResponse.model_fields


# ---------------------------------------------------------------------------
# Shared fixtures for DB tests
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
# T-12: Preview (SC-PRV-04) — synchronous, no DB
# ---------------------------------------------------------------------------


class TestPreview:
    """SC-PRV-04: preview() renders both subject and body, no DB write."""

    def _make_service(self):
        db = MagicMock()
        return ComunicacionService(db, uuid4())

    def test_preview_renders_asunto_and_cuerpo(self):
        svc = self._make_service()
        req = ComunicacionPreviewRequest(
            asunto_template="Hola $nombre",
            cuerpo_template="Tenés $actividades_faltantes pendientes.",
            variables={"nombre": "Maria", "actividades_faltantes": "TP1"},
        )
        resp = svc.preview(req)
        assert resp.asunto_renderizado == "Hola Maria"
        assert resp.cuerpo_renderizado == "Tenés TP1 pendientes."

    def test_preview_missing_var_left_as_literal(self):
        svc = self._make_service()
        req = ComunicacionPreviewRequest(
            asunto_template="Hola $nombre",
            cuerpo_template="Materia: $materia",
            variables={},
        )
        resp = svc.preview(req)
        assert "$nombre" in resp.asunto_renderizado
        assert "$materia" in resp.cuerpo_renderizado


# ---------------------------------------------------------------------------
# T-13: encolar (SC-ENQ-01, SC-ENQ-02, SC-ENQ-03) — requires DB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_encolar_single_recipient_estado_pendiente(db_session):
    """SC-ENQ-01: single recipient → 1 row, estado=Pendiente, lote_id=None."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    await db_session.commit()

    current_user = MagicMock()
    current_user.id = user.id
    current_user.tenant_id = tenant.id

    from app.schemas.comunicacion import ComunicacionEnviarRequest, DestinatarioItem

    req = ComunicacionEnviarRequest(
        asunto_template="Hola $nombre",
        cuerpo_template="Pendientes: $actividades_faltantes",
        destinatarios=[DestinatarioItem(email="student@test.com", nombre="Ana", actividades_faltantes="TP1")],
        materia_id=materia.id,
    )

    svc = ComunicacionService(db_session, tenant.id)
    rows = await svc.encolar(req, current_user)

    assert len(rows) == 1
    row = rows[0]
    assert row.estado == EstadoComunicacion.PENDIENTE
    assert row.lote_id is None
    assert row.enviado_por == user.id


@pytest.mark.asyncio
async def test_encolar_multiple_recipients_share_lote_id(db_session):
    """SC-ENQ-02: multiple recipients → rows share same non-null lote_id."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    await db_session.commit()

    current_user = MagicMock()
    current_user.id = user.id
    current_user.tenant_id = tenant.id

    from app.schemas.comunicacion import ComunicacionEnviarRequest, DestinatarioItem

    req = ComunicacionEnviarRequest(
        asunto_template="Hola $nombre",
        cuerpo_template="Pendientes: $actividades_faltantes",
        destinatarios=[
            DestinatarioItem(email="a@test.com", nombre="A", actividades_faltantes="TP1"),
            DestinatarioItem(email="b@test.com", nombre="B", actividades_faltantes="TP2"),
            DestinatarioItem(email="c@test.com", nombre="C", actividades_faltantes="TP3"),
        ],
        materia_id=materia.id,
    )

    svc = ComunicacionService(db_session, tenant.id)
    rows = await svc.encolar(req, current_user)

    assert len(rows) == 3
    lote_ids = {r.lote_id for r in rows}
    assert len(lote_ids) == 1
    assert None not in lote_ids


@pytest.mark.asyncio
async def test_encolar_tenant_with_approval_required_aprobado_false(db_session):
    """SC-ENQ-03: tenant with aprobacion=True → batch rows have aprobado=False."""
    tenant = await _make_tenant(db_session, aprobacion=True)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    await db_session.commit()

    current_user = MagicMock()
    current_user.id = user.id
    current_user.tenant_id = tenant.id

    from app.schemas.comunicacion import ComunicacionEnviarRequest, DestinatarioItem

    req = ComunicacionEnviarRequest(
        asunto_template="Hola $nombre",
        cuerpo_template="Pendientes: $actividades_faltantes",
        destinatarios=[
            DestinatarioItem(email="a@test.com", nombre="A", actividades_faltantes="TP1"),
            DestinatarioItem(email="b@test.com", nombre="B", actividades_faltantes="TP2"),
        ],
        materia_id=materia.id,
    )

    svc = ComunicacionService(db_session, tenant.id)
    rows = await svc.encolar(req, current_user)

    assert all(r.aprobado is False for r in rows)


# ---------------------------------------------------------------------------
# T-14: aprobacion (SC-APR-01, SC-APR-02)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aprobar_lote_enables_dispatch(db_session):
    """SC-APR-01: aprovando lote → all PENDIENTE rows get aprobado=True."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    c1 = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=lote_id)
    c2 = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=lote_id)
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    count = await svc.aprobar_lote(lote_id, tenant.id)

    await db_session.refresh(c1)
    await db_session.refresh(c2)

    assert count == 2
    assert c1.aprobado is True
    assert c2.aprobado is True


@pytest.mark.asyncio
async def test_aprobar_lote_only_affects_pendiente_rows(db_session):
    """SC-APR-02: batch approval only flips PENDIENTE rows, not ENVIADO."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    c_pend = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id, lote_id=lote_id
    )
    c_env = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, lote_id=lote_id
    )
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    count = await svc.aprobar_lote(lote_id, tenant.id)

    await db_session.refresh(c_pend)
    await db_session.refresh(c_env)

    assert count == 1
    assert c_pend.aprobado is True
    assert c_env.aprobado is False


@pytest.mark.asyncio
async def test_aprobar_individual_idempotent_on_enviado(db_session):
    """SC-APR-02 (individual): ENVIADO row → no-op, returns row, HTTP 200 (no error)."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO, aprobado=False
    )
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    row = await svc.aprobar_individual(c.id, tenant.id)

    assert row.id == c.id
    assert row.estado == EstadoComunicacion.ENVIADO


@pytest.mark.asyncio
async def test_aprobar_individual_pendiente_sets_aprobado(db_session):
    """aprobar_individual on PENDIENTE row sets aprobado=True."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE, aprobado=False
    )
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    row = await svc.aprobar_individual(c.id, tenant.id)

    await db_session.refresh(c)
    assert row.aprobado is True


# ---------------------------------------------------------------------------
# T-15: cancelacion (SC-CAN-01, SC-CAN-02)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancelar_lote_transitions_pendiente_to_cancelado(db_session):
    """SC-CAN-01: cancel lote → all PENDIENTE rows → CANCELADO."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)
    lote_id = uuid4()

    c1 = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=lote_id)
    c2 = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=lote_id)
    c3 = await _make_comunicacion(db_session, tenant.id, user.id, materia.id, lote_id=lote_id)
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    count = await svc.cancelar_lote(lote_id, tenant.id)

    await db_session.refresh(c1)
    await db_session.refresh(c2)
    await db_session.refresh(c3)

    assert count == 3
    assert all(r.estado == EstadoComunicacion.CANCELADO for r in [c1, c2, c3])


@pytest.mark.asyncio
async def test_cancelar_individual_enviado_raises_service_error(db_session):
    """SC-CAN-02: cancelling an ENVIADO row raises ServiceError (→ HTTP 409)."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIADO
    )
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    with pytest.raises(ServiceError):
        await svc.cancelar_individual(c.id, tenant.id)


@pytest.mark.asyncio
async def test_cancelar_individual_enviando_raises_service_error(db_session):
    """Cancelling an ENVIANDO row raises ServiceError (in-flight guard)."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.ENVIANDO
    )
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    with pytest.raises(ServiceError):
        await svc.cancelar_individual(c.id, tenant.id)


@pytest.mark.asyncio
async def test_cancelar_individual_pendiente_succeeds(db_session):
    """Cancelling a PENDIENTE row → CANCELADO state, no error."""
    tenant = await _make_tenant(db_session)
    user = await _make_user(db_session, tenant.id)
    materia = await _make_materia(db_session, tenant.id)

    c = await _make_comunicacion(
        db_session, tenant.id, user.id, materia.id,
        estado=EstadoComunicacion.PENDIENTE
    )
    await db_session.commit()

    svc = ComunicacionService(db_session, tenant.id)
    row = await svc.cancelar_individual(c.id, tenant.id)

    assert row.estado == EstadoComunicacion.CANCELADO
