import pytest
import uuid
from datetime import datetime
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.carrera import Carrera
from app.models.materia import Materia
from app.models.cohorte import Cohorte


@pytest.fixture
async def programa_setup(db_session):
    tenant_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Tenant Test")
    db_session.add(tenant)
    await db_session.flush()

    carrera = Carrera(tenant_id=tenant_id, codigo="CAR", nombre="Carrera")
    materia = Materia(tenant_id=tenant_id, codigo="MAT", nombre="Materia")
    db_session.add_all([carrera, materia])
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant_id, carrera_id=carrera.id, nombre="Cohorte", anio=2026,
        vig_desde=datetime(2026, 1, 1).date(), vig_hasta=datetime(2026, 12, 31).date(),
    )
    db_session.add(cohorte)
    await db_session.flush()
    await db_session.commit()

    return {
        "tenant_id": tenant_id,
        "admin_id": admin_id,
        "materia_id": materia.id,
        "carrera_id": carrera.id,
        "cohorte_id": cohorte.id,
    }


@pytest.mark.asyncio
async def test_subir_listar_descargar_programa(db_session, monkeypatch, programa_setup):
    """HU-23: subir, listar y descargar el programa de una materia."""
    setup = programa_setup
    mock_admin = CurrentUser(
        id=setup["admin_id"], tenant_id=setup["tenant_id"],
        email="admin@test.com", roles=["COORDINADOR"],
    )

    async def mock_perms(*args, **kwargs):
        return ["estructura:gestionar"]

    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_perms,
    )
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_admin

    pdf_bytes = b"%PDF-1.4 contenido de prueba"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("programa.pdf", pdf_bytes, "application/pdf")}
        data = {
            "materia_id": str(setup["materia_id"]),
            "carrera_id": str(setup["carrera_id"]),
            "cohorte_id": str(setup["cohorte_id"]),
            "titulo": "Programa 2026",
        }
        res = await ac.post("/api/v1/programas/", data=data, files=files, headers={"Authorization": "Bearer mock"})
        assert res.status_code == 201
        creado = res.json()
        assert creado["titulo"] == "Programa 2026"
        assert creado["file_size"] == len(pdf_bytes)
        programa_id = creado["id"]

        listado = await ac.get(
            "/api/v1/programas/",
            params={"materia_id": str(setup["materia_id"])},
            headers={"Authorization": "Bearer mock"},
        )
        assert listado.status_code == 200
        assert len(listado.json()) == 1

        descarga = await ac.get(f"/api/v1/programas/{programa_id}/download", headers={"Authorization": "Bearer mock"})
        assert descarga.status_code == 200
        assert descarga.content == pdf_bytes

    app.dependency_overrides.clear()
