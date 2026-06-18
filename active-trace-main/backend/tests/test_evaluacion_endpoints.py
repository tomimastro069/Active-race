import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.carrera import Carrera
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.evaluacion import Evaluacion, EvaluacionTipoEnum
from app.core.security import generate_email_hash

@pytest.fixture
async def evaluacion_api_setup(db_session):
    tenant_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    alumno_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Tenant Test")
    db_session.add(tenant)
    await db_session.flush()

    admin = Usuario(
        id=admin_id,
        tenant_id=tenant_id,
        email="admin@test.com",
        email_hash=generate_email_hash("admin@test.com"),
        hashed_password="pwd"
    )
    alumno = Usuario(
        id=alumno_id,
        tenant_id=tenant_id,
        email="alumno@test.com",
        email_hash=generate_email_hash("alumno@test.com"),
        hashed_password="pwd"
    )
    db_session.add_all([admin, alumno])
    await db_session.flush()

    carrera = Carrera(tenant_id=tenant.id, codigo="CAR", nombre="Carrera")
    materia = Materia(tenant_id=tenant.id, codigo="MAT", nombre="Materia")
    db_session.add_all([carrera, materia])
    await db_session.flush()

    cohorte = Cohorte(tenant_id=tenant.id, carrera_id=carrera.id, nombre="Cohorte", anio=2026, vig_desde=datetime(2026, 1, 1).date(), vig_hasta=datetime(2026, 12, 31).date())
    db_session.add(cohorte)
    await db_session.flush()

    eval_obj = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo=EvaluacionTipoEnum.COLOQUIO,
        instancia="Coloquio Final",
        dias_disponibles=2,
        cupos_totales=2
    )
    db_session.add(eval_obj)
    await db_session.flush()

    await db_session.commit()

    return {
        "tenant_id": tenant_id,
        "admin_id": admin_id,
        "alumno_id": alumno_id,
        "evaluacion_id": eval_obj.id,
        "materia_id": materia.id,
        "cohorte_id": cohorte.id
    }

@pytest.mark.asyncio
async def test_crear_evaluacion_endpoint(db_session, monkeypatch, evaluacion_api_setup):
    setup = evaluacion_api_setup

    mock_admin = CurrentUser(
        id=setup["admin_id"],
        tenant_id=setup["tenant_id"],
        email="admin@test.com",
        roles=["ADMIN"]
    )

    async def mock_get_admin_perms(*args, **kwargs):
        return ["encuentros:gestionar"] # Arbitrary permission to manage evaluations
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_admin_perms
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_admin

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "materia_id": str(setup["materia_id"]),
            "cohorte_id": str(setup["cohorte_id"]),
            "tipo": "Coloquio",
            "instancia": "Coloquio 2",
            "dias_disponibles": 3,
            "cupos_totales": 15
        }
        res = await ac.post("/api/v1/admin/evaluaciones/", json=payload, headers={"Authorization": "Bearer mock"})
        assert res.status_code == 201
        data = res.json()
        assert data["instancia"] == "Coloquio 2"
        assert data["cupos_totales"] == 15

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_reservar_evaluacion_endpoint(db_session, monkeypatch, evaluacion_api_setup):
    setup = evaluacion_api_setup

    mock_alumno = CurrentUser(
        id=setup["alumno_id"],
        tenant_id=setup["tenant_id"],
        email="alumno@test.com",
        roles=["ALUMNO"]
    )

    async def mock_get_alumno_perms(*args, **kwargs):
        return [] # Alumno doesn't need specific backend perms typically, but uses endpoint scoping
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_alumno_perms
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_alumno

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "evaluacion_id": str(setup["evaluacion_id"]),
            "alumno_id": str(setup["alumno_id"]),
            "fecha_hora": "2026-07-06T10:00:00Z"
        }
        res = await ac.post("/api/v1/reservas/evaluaciones/", json=payload, headers={"Authorization": "Bearer mock"})
        assert res.status_code == 201
        data = res.json()
        assert data["evaluacion_id"] == str(setup["evaluacion_id"])
        assert data["alumno_id"] == str(setup["alumno_id"])

        # Try duplicate
        res_dup = await ac.post("/api/v1/reservas/evaluaciones/", json=payload, headers={"Authorization": "Bearer mock"})
        assert res_dup.status_code == 400
        assert "activa" in res_dup.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.fixture
def _override_admin(db_session, monkeypatch):
    """Helper: monta overrides de DB + admin con permiso encuentros:gestionar."""
    def _apply(setup):
        mock_admin = CurrentUser(
            id=setup["admin_id"],
            tenant_id=setup["tenant_id"],
            email="admin@test.com",
            roles=["ADMIN"],
        )

        async def mock_perms(*args, **kwargs):
            return ["encuentros:gestionar"]

        monkeypatch.setattr(
            "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
            mock_perms,
        )
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: mock_admin
    return _apply


@pytest.mark.asyncio
async def test_listar_evaluaciones_con_contadores(db_session, evaluacion_api_setup, _override_admin):
    """HU-31: el listado expone convocados / reservas activas / cupos disponibles."""
    setup = evaluacion_api_setup
    _override_admin(setup)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/evaluaciones/", headers={"Authorization": "Bearer mock"})
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        fila = data[0]
        assert fila["convocados"] == 0
        assert fila["reservas_activas"] == 0
        assert fila["cupos_disponibles"] == fila["cupos_totales"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_importar_convocados(db_session, evaluacion_api_setup, _override_admin):
    """HU-30: importar el padrón de elegibles del coloquio es idempotente."""
    setup = evaluacion_api_setup
    _override_admin(setup)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        url = f"/api/v1/admin/evaluaciones/{setup['evaluacion_id']}/convocados"
        payload = {"alumno_ids": [str(setup["alumno_id"])]}
        res = await ac.post(url, json=payload, headers={"Authorization": "Bearer mock"})
        assert res.status_code == 201
        assert res.json()["convocados_nuevos"] == 1

        # Reimportar el mismo alumno no duplica
        res2 = await ac.post(url, json=payload, headers={"Authorization": "Bearer mock"})
        assert res2.status_code == 201
        assert res2.json()["convocados_nuevos"] == 0
        assert res2.json()["convocados_totales"] == 1
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_agenda_y_registro_academico(db_session, evaluacion_api_setup, _override_admin):
    """HU-32 agenda de reservas + HU-33 registro académico consolidado."""
    setup = evaluacion_api_setup
    _override_admin(setup)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Generar una reserva
        await ac.post(
            "/api/v1/reservas/evaluaciones/",
            json={
                "evaluacion_id": str(setup["evaluacion_id"]),
                "alumno_id": str(setup["alumno_id"]),
                "fecha_hora": "2026-07-06T10:00:00Z",
            },
            headers={"Authorization": "Bearer mock"},
        )
        # Agenda (HU-32)
        agenda = await ac.get("/api/v1/reservas/agenda", headers={"Authorization": "Bearer mock"})
        assert agenda.status_code == 200
        assert len(agenda.json()) == 1
        assert agenda.json()[0]["alumno_id"] == str(setup["alumno_id"])

        # Cargar nota final (HU-33)
        res_nota = await ac.post(
            f"/api/v1/admin/evaluaciones/{setup['evaluacion_id']}/resultados",
            json={"alumno_id": str(setup["alumno_id"]), "nota_final": "8"},
            headers={"Authorization": "Bearer mock"},
        )
        assert res_nota.status_code == 201
        assert res_nota.json()["nota_final"] == "8"

        # Registro académico consolidado (HU-33)
        registro = await ac.get("/api/v1/admin/evaluaciones/registro", headers={"Authorization": "Bearer mock"})
        assert registro.status_code == 200
        assert len(registro.json()) == 1
        assert registro.json()[0]["nota_final"] == "8"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_fechas_y_cronograma(db_session, evaluacion_api_setup, _override_admin):
    """HU-24: alta con fecha/título, listado por fecha y cronograma embebible."""
    setup = evaluacion_api_setup
    _override_admin(setup)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "materia_id": str(setup["materia_id"]),
            "cohorte_id": str(setup["cohorte_id"]),
            "tipo": "Parcial",
            "instancia": "1",
            "titulo": "Primer Parcial",
            "fecha": "2026-09-15",
            "dias_disponibles": 1,
            "cupos_totales": 30,
        }
        res = await ac.post("/api/v1/admin/evaluaciones/", json=payload, headers={"Authorization": "Bearer mock"})
        assert res.status_code == 201
        assert res.json()["fecha"] == "2026-09-15"
        assert res.json()["titulo"] == "Primer Parcial"

        # Cronograma embebible (HU-24)
        crono = await ac.get(
            f"/api/v1/admin/evaluaciones/cronograma/{setup['materia_id']}",
            headers={"Authorization": "Bearer mock"},
        )
        assert crono.status_code == 200
        assert "Primer Parcial" in crono.text
        assert "15/09/2026" in crono.text
    app.dependency_overrides.clear()
