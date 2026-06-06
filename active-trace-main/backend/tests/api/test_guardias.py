import pytest
import uuid
from datetime import time, datetime
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.materia import Materia
from app.models.rol import Rol
from app.models.asignacion import Asignacion

@pytest.mark.asyncio
async def test_guardias_api_flow(db_session, monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Test Tenant")
    actor = Usuario(id=actor_id, tenant_id=tenant_id, email="tutor@example.com", hashed_password="pass")
    materia = Materia(tenant_id=tenant_id, codigo="MAT1", nombre="Materia 1")
    rol = Rol(tenant_id=tenant_id, nombre="TUTOR")
    db_session.add_all([tenant, actor, materia, rol])
    await db_session.commit()

    asignacion = Asignacion(
        tenant_id=tenant_id,
        usuario_id=actor_id,
        rol_id=rol.id,
        materia_id=materia.id,
        desde=datetime(2026, 6, 1)
    )
    db_session.add(asignacion)
    await db_session.commit()

    # Mock permissions to allow managing encounters/guardias
    async def mock_get_perms(*args, **kwargs):
        return ["encuentros:gestionar"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_perms
    )

    mock_user = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="tutor@example.com",
        roles=["TUTOR"]
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    headers = {"Authorization": "Bearer fake_token"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register a Guardia (POST)
        payload = {
            "materia_id": str(materia.id),
            "asignacion_id": str(asignacion.id),
            "dia_semana": "Martes",
            "hora_inicio": "14:00:00",
            "hora_fin": "14:45:00"
        }
        res_create = await ac.post("/api/v1/guardias/", json=payload, headers=headers)
        assert res_create.status_code == 201
        data_create = res_create.json()
        assert data_create["estado"] == "Pendiente"
        guardia_id = data_create["id"]

        # 2. Get list of Guardias (GET)
        res_list = await ac.get("/api/v1/guardias/", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1

        # 3. Approve Guardia (POST /aprobar)
        res_approve = await ac.post(f"/api/v1/guardias/{guardia_id}/aprobar", json={}, headers=headers)
        assert res_approve.status_code == 200
        assert res_approve.json()["estado"] == "Aprobada"

    app.dependency_overrides.clear()
