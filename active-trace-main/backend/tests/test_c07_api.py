import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.asignacion import Asignacion
from app.core.security import generate_email_hash

@pytest.mark.asyncio
async def test_usuarios_api_permissions_and_masking(db_session, monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    # Seed Tenant and Actor in DB
    tenant = Tenant(id=tenant_id, name="Tenant Test")
    actor = Usuario(
        id=actor_id,
        tenant_id=tenant_id,
        email="admin_user@example.com",
        email_hash=generate_email_hash("admin_user@example.com"),
        hashed_password="pwd"
    )
    db_session.add_all([tenant, actor])
    await db_session.commit()

    # Mock CurrentUser
    mock_admin = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="admin_user@example.com",
        roles=["ADMIN"]
    )

    # 1. Access without permission (mock empty permissions)
    async def mock_get_no_perms(*args, **kwargs):
        return []
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_no_perms
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_admin

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create attempt - should be blocked (403)
        res_create_denied = await ac.post("/api/v1/admin/usuarios/", json={
            "email": "nuevo@example.com",
            "password": "password123"
        })
        assert res_create_denied.status_code == 403

    # 2. Access with proper permission
    async def mock_get_admin_perms(*args, **kwargs):
        return ["usuarios:gestionar"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_admin_perms
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create User
        payload = {
            "email": "juan.perez.api@example.com",
            "password": "securepassword123",
            "nombre": "Juan",
            "apellidos": "Pérez",
            "dni": "12345678",
            "cuil": "20-12345678-9",
            "facturador": True
        }
        res_create = await ac.post("/api/v1/admin/usuarios/", json=payload)
        assert res_create.status_code == 201
        data = res_create.json()
        assert data["email"] == "juan.perez.api@example.com"
        assert data["nombre"] == "Juan"
        # Verify PII masking on creation return
        assert data["dni"] == f"*****5678"
        assert data["cuil"] == f"*****78-9"
        
        new_user_id = data["id"]

        # List Users
        res_list = await ac.get("/api/v1/admin/usuarios/")
        assert res_list.status_code == 200
        list_data = res_list.json()
        # Find created user in list
        filtered = [u for u in list_data if u["id"] == new_user_id]
        assert len(filtered) == 1
        assert filtered[0]["dni"] == f"*****5678"  # Masked!

        # Get User
        res_get = await ac.get(f"/api/v1/admin/usuarios/{new_user_id}")
        assert res_get.status_code == 200
        get_data = res_get.json()
        assert get_data["dni"] == f"*****5678"  # Masked!

        # Update User
        update_payload = {
            "nombre": "Juan C",
            "dni": "87654321"
        }
        res_patch = await ac.patch(f"/api/v1/admin/usuarios/{new_user_id}", json=update_payload)
        assert res_patch.status_code == 200
        patch_data = res_patch.json()
        assert patch_data["nombre"] == "Juan C"
        assert patch_data["dni"] == f"*****4321"  # Masked!

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_asignaciones_api_permissions_and_crud(db_session, monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    target_user_id = uuid.uuid4()

    # Seed Tenant and Users
    tenant = Tenant(id=tenant_id, name="Tenant Test")
    actor = Usuario(
        id=actor_id,
        tenant_id=tenant_id,
        email="coord_asig@example.com",
        email_hash=generate_email_hash("coord_asig@example.com"),
        hashed_password="pwd"
    )
    target = Usuario(
        id=target_user_id,
        tenant_id=tenant_id,
        email="docente_asig@example.com",
        email_hash=generate_email_hash("docente_asig@example.com"),
        hashed_password="pwd"
    )
    rol = Rol(
        tenant_id=tenant_id,
        nombre="PROFESOR"
    )
    db_session.add_all([tenant, actor, target, rol])
    await db_session.commit()

    # Mock CurrentUser
    mock_actor = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="coord_asig@example.com",
        roles=["COORDINADOR"]
    )

    # 1. Try creating without permission
    async def mock_get_no_perms(*args, **kwargs):
        return []
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_no_perms
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_actor

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_create_denied = await ac.post("/api/v1/asignaciones/", json={
            "usuario_id": str(target_user_id),
            "rol_id": str(rol.id),
            "desde": datetime.utcnow().isoformat()
        })
        assert res_create_denied.status_code == 403

    # 2. Access with proper permission
    async def mock_get_asig_perms(*args, **kwargs):
        return ["equipos:asignar"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_asig_perms
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Assignment
        payload = {
            "usuario_id": str(target_user_id),
            "rol_id": str(rol.id),
            "desde": datetime.utcnow().isoformat(),
            "hasta": (datetime.utcnow() + pytest.importorskip("datetime").timedelta(days=10)).isoformat()
        }
        res_create = await ac.post("/api/v1/asignaciones/", json=payload)
        assert res_create.status_code == 201
        data = res_create.json()
        assert data["usuario_id"] == str(target_user_id)
        assert data["rol_id"] == str(rol.id)
        assert data["estado_vigencia"] == "Vigente"
        asig_id = data["id"]

        # List Assignments
        res_list = await ac.get("/api/v1/asignaciones/", params={"usuario_id": str(target_user_id)})
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1
        assert res_list.json()[0]["id"] == asig_id

        # Get Assignment
        res_get = await ac.get(f"/api/v1/asignaciones/{asig_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == asig_id

        # Update Assignment
        update_payload = {
            "hasta": datetime.utcnow().isoformat()  # Expire it now
        }
        res_patch = await ac.patch(f"/api/v1/asignaciones/{asig_id}", json=update_payload)
        assert res_patch.status_code == 200
        # Wait, the response might be cached or computed, but it should say Vencida because hasta is <= now
        # Actually since the time when we fetch and compare might be microsecond-based, let's set it in the past to be safe
        update_payload_past = {
            "desde": (datetime.utcnow() - pytest.importorskip("datetime").timedelta(days=10)).isoformat(),
            "hasta": (datetime.utcnow() - pytest.importorskip("datetime").timedelta(days=5)).isoformat()
        }
        res_patch_past = await ac.patch(f"/api/v1/asignaciones/{asig_id}", json=update_payload_past)
        assert res_patch_past.status_code == 200
        assert res_patch_past.json()["estado_vigencia"] == "Vencida"

        # Delete Assignment (logical)
        res_del = await ac.delete(f"/api/v1/asignaciones/{asig_id}")
        assert res_del.status_code == 204

        # Get should now return 404 (because of logical deletion filtering)
        res_get_deleted = await ac.get(f"/api/v1/asignaciones/{asig_id}")
        assert res_get_deleted.status_code == 404

    app.dependency_overrides.clear()
