import pytest
import uuid
from datetime import date, time, datetime
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.materia import Materia

@pytest.mark.asyncio
async def test_encuentros_api_flow(db_session, monkeypatch):
    # Setup Tenant and Materia
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Test Tenant")
    actor = Usuario(id=actor_id, tenant_id=tenant_id, email="profesor@example.com", hashed_password="pass")
    materia = Materia(tenant_id=tenant_id, codigo="MAT1", nombre="Materia 1")
    db_session.add_all([tenant, actor, materia])
    await db_session.commit()

    # Mock permissions to allow managing encounters
    async def mock_get_perms(*args, **kwargs):
        return ["encuentros:gestionar"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_perms
    )

    mock_user = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="profesor@example.com",
        roles=["PROFESOR"]
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    headers = {"Authorization": "Bearer fake_token"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create recurrent slot and instances (POST)
        payload = {
            "materia_id": str(materia.id),
            "titulo": "Clase de consulta",
            "hora": "18:00:00",
            "dia_semana": "Lunes",
            "fecha_inicio": "2026-06-08",
            "cant_semanas": 3,
            "meet_url": "https://meet.google.com/abc-defg-hij"
        }
        res_create = await ac.post("/api/v1/encuentros/recurrentes", json=payload, headers=headers)
        assert res_create.status_code == 201
        data_create = res_create.json()
        assert data_create["slot"]["titulo"] == "Clase de consulta"
        assert len(data_create["instancias"]) == 3
        instancia_id = data_create["instancias"][0]["id"]

        # 2. Get list of instances for a materia
        res_list = await ac.get(f"/api/v1/encuentros/materias/{materia.id}", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) == 3

        # 3. Update meet URL and record video URL of an instance (PATCH)
        update_payload = {
            "estado": "Realizado",
            "video_url": "https://drive.google.com/video123"
        }
        res_update = await ac.patch(f"/api/v1/encuentros/instancias/{instancia_id}", json=update_payload, headers=headers)
        assert res_update.status_code == 200
        assert res_update.json()["estado"] == "Realizado"
        assert res_update.json()["video_url"] == "https://drive.google.com/video123"

        # 4. Export to HTML
        res_html = await ac.get(f"/api/v1/encuentros/exportar/{materia.id}", headers=headers)
        assert res_html.status_code == 200
        assert "text/html" in res_html.headers["content-type"]
        assert "Clase de consulta" in res_html.text

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_encuentros_api_forbidden(db_session):
    # Setup Tenant and Materia
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Test Tenant")
    actor = Usuario(id=actor_id, tenant_id=tenant_id, email="alumno@example.com", hashed_password="pass")
    db_session.add_all([tenant, actor])
    await db_session.commit()

    # User without "encuentros:gestionar"
    mock_user = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="alumno@example.com",
        roles=["ALUMNO"]
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    headers = {"Authorization": "Bearer fake_token"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "materia_id": str(uuid.uuid4()),
            "titulo": "Clase de consulta",
            "hora": "18:00:00",
            "dia_semana": "Lunes",
            "fecha_inicio": "2026-06-08",
            "cant_semanas": 3,
            "meet_url": "https://meet.google.com/abc-defg-hij"
        }
        res_create = await ac.post("/api/v1/encuentros/recurrentes", json=payload, headers=headers)
        assert res_create.status_code == 403

    app.dependency_overrides.clear()
