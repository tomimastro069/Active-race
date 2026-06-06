import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.tarea import Tarea, EstadoTareaEnum

@pytest.mark.asyncio
async def test_tareas_api_endpoints(db_session, monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    tutor_id = uuid.uuid4()
    materia_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Test Tenant")
    actor = Usuario(id=actor_id, tenant_id=tenant_id, email="coordinator@example.com", hashed_password="pwd")
    tutor = Usuario(id=tutor_id, tenant_id=tenant_id, email="tutor@example.com", hashed_password="pwd")
    
    db_session.add_all([tenant, actor, tutor])
    await db_session.commit()

    # Mock permissions to simulate 'tareas:gestionar'
    async def mock_get_effective_permissions(*args, **kwargs):
        return ["tareas:gestionar", "tareas:gestionar_propio"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_effective_permissions
    )

    mock_docente = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="coordinator@example.com",
        roles=["COORDINADOR"]
    )
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_docente

    headers = {"Authorization": "Bearer mock-token"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Tarea
        payload = {
            "descripcion": "Corregir TPs",
            "materia_id": str(materia_id),
            "asignado_a": str(tutor_id)
        }
        res = await ac.post("/api/v1/tareas/", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        tarea_id = data["id"]
        assert data["estado"] == "Pendiente"
        assert data["asignado_a"] == str(tutor_id)
        assert data["asignado_por"] == str(actor_id)
        
        # 2. List Tareas
        res_list = await ac.get("/api/v1/tareas/", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1
        
        # 3. Get Tarea
        res_get = await ac.get(f"/api/v1/tareas/{tarea_id}", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["descripcion"] == "Corregir TPs"
        
        # 4. Update Tarea State
        update_payload = {"estado": "En progreso"}
        res_patch = await ac.patch(f"/api/v1/tareas/{tarea_id}", json=update_payload, headers=headers)
        assert res_patch.status_code == 200
        assert res_patch.json()["estado"] == "En progreso"
        
        # 5. Add Comentario
        comentario_payload = {"texto": "Comenzando a corregir"}
        res_com_post = await ac.post(f"/api/v1/tareas/{tarea_id}/comentarios", json=comentario_payload, headers=headers)
        assert res_com_post.status_code == 201
        assert res_com_post.json()["texto"] == "Comenzando a corregir"
        
        # 6. List Comentarios
        res_com_list = await ac.get(f"/api/v1/tareas/{tarea_id}/comentarios", headers=headers)
        assert res_com_list.status_code == 200
        assert len(res_com_list.json()) == 1

    app.dependency_overrides.clear()
