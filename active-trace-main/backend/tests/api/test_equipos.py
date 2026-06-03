import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timedelta
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.asignacion import Asignacion
from app.core.security import generate_email_hash

@pytest.mark.asyncio
async def test_equipos_api_endpoints(db_session, monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()

    # Seed Tenant, Actor, and Users
    tenant = Tenant(id=tenant_id, name="API Equipos Tenant")
    actor = Usuario(
        id=actor_id,
        tenant_id=tenant_id,
        email="coord_equipos@example.com",
        email_hash=generate_email_hash("coord_equipos@example.com"),
        hashed_password="pwd"
    )
    user1 = Usuario(
        id=user1_id,
        tenant_id=tenant_id,
        email="user1_eq@example.com",
        email_hash=generate_email_hash("user1_eq@example.com"),
        hashed_password="pwd",
        nombre="Juan",
        apellidos="Pérez"
    )
    user2 = Usuario(
        id=user2_id,
        tenant_id=tenant_id,
        email="user2_eq@example.com",
        email_hash=generate_email_hash("user2_eq@example.com"),
        hashed_password="pwd",
        nombre="Maria",
        apellidos="Gomez"
    )
    rol = Rol(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        nombre="PROFESOR"
    )
    db_session.add_all([tenant, actor, user1, user2, rol])
    await db_session.commit()

    # Mock CurrentUser for Coord
    mock_coord = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="coord_equipos@example.com",
        roles=["COORDINADOR"]
    )

    async def mock_get_asig_perms(*args, **kwargs):
        return ["equipos:asignar"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_asig_perms
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_coord

    materia_id = uuid.uuid4()
    cohorte_id = uuid.uuid4()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Mass Assignment (POST /api/v1/equipos/masiva)
        payload_masiva = {
            "usuario_ids": [str(user1_id), str(user2_id)],
            "rol_id": str(rol.id),
            "materia_id": str(materia_id),
            "cohorte_id": str(cohorte_id),
            "desde": datetime.utcnow().isoformat()
        }
        res_masiva = await ac.post("/api/v1/equipos/masiva", json=payload_masiva)
        assert res_masiva.status_code == 201
        data_masiva = res_masiva.json()
        assert len(data_masiva) == 2
        assert {d["usuario_id"] for d in data_masiva} == {str(user1_id), str(user2_id)}

        # 2. Validity update (PATCH /api/v1/equipos/vigencia)
        new_hasta = (datetime.utcnow() + timedelta(days=10)).isoformat()
        payload_vigencia = {
            "materia_id": str(materia_id),
            "cohorte_id": str(cohorte_id),
            "hasta": new_hasta
        }
        res_vig = await ac.patch("/api/v1/equipos/vigencia", json=payload_vigencia)
        assert res_vig.status_code == 200
        assert len(res_vig.json()) == 2

        # 3. Export CSV (GET /api/v1/equipos/exportar)
        res_exp = await ac.get("/api/v1/equipos/exportar", params={"materia_id": str(materia_id)})
        assert res_exp.status_code == 200
        assert res_exp.headers["Content-Type"] == "text/csv; charset=utf-8"
        assert "Juan" in res_exp.text
        assert "Maria" in res_exp.text
        assert "PROFESOR" in res_exp.text

        # 4. Clone Team (POST /api/v1/equipos/clonar)
        target_materia = uuid.uuid4()
        target_cohorte = uuid.uuid4()
        payload_clonar = {
            "source_materia_id": str(materia_id),
            "source_cohorte_id": str(cohorte_id),
            "target_materia_id": str(target_materia),
            "target_cohorte_id": str(target_cohorte),
            "nuevo_desde": datetime.utcnow().isoformat()
        }
        res_clone = await ac.post("/api/v1/equipos/clonar", json=payload_clonar)
        assert res_clone.status_code == 201
        assert len(res_clone.json()) == 2

        # 5. Clone Conflict (destination already has assignments)
        res_clone_conflict = await ac.post("/api/v1/equipos/clonar", json=payload_clonar)
        assert res_clone_conflict.status_code == 409
        assert "El contexto destino ya tiene asignaciones activas" in res_clone_conflict.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_mis_equipos_api_scope(db_session, monkeypatch):
    """Test GET /api/v1/equipos/mis-equipos ensures IDOR prevention by returning active user's assignments only."""
    tenant_id = uuid.uuid4()
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    # Seed Tenant and Users
    tenant = Tenant(id=tenant_id, name="Mis Equipos Tenant")
    user_a = Usuario(
        id=user_a_id,
        tenant_id=tenant_id,
        email="user_a@example.com",
        email_hash=generate_email_hash("user_a@example.com"),
        hashed_password="pwd"
    )
    user_b = Usuario(
        id=user_b_id,
        tenant_id=tenant_id,
        email="user_b@example.com",
        email_hash=generate_email_hash("user_b@example.com"),
        hashed_password="pwd"
    )
    rol = Rol(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        nombre="PROFESOR"
    )
    db_session.add_all([tenant, user_a, user_b, rol])
    await db_session.commit()

    # Create assignment for A
    asig_a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user_a_id,
        rol_id=rol.id,
        desde=datetime.utcnow()
    )
    # Create assignment for B
    asig_b = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user_b_id,
        rol_id=rol.id,
        desde=datetime.utcnow()
    )
    db_session.add_all([asig_a, asig_b])
    await db_session.commit()

    # Setup overrides and mock User A
    mock_user_a = CurrentUser(
        id=user_a_id,
        tenant_id=tenant_id,
        email="user_a@example.com",
        roles=["PROFESOR"]
    )
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user_a

    # No permission required for mis-equipos, but mock empty permissions to prove it bypasses require_permission("equipos:asignar")
    async def mock_get_no_perms(*args, **kwargs):
        return []
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_no_perms
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Request User A's teams
        res_a = await ac.get("/api/v1/equipos/mis-equipos")
        assert res_a.status_code == 200
        data_a = res_a.json()
        # Should return exactly 1 assignment, belonging to User A
        assert len(data_a) == 1
        assert data_a[0]["usuario_id"] == str(user_a_id)

        # Force User B's mock to see if switching identity is securely separated
        mock_user_b = CurrentUser(
            id=user_b_id,
            tenant_id=tenant_id,
            email="user_b@example.com",
            roles=["PROFESOR"]
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user_b

        res_b = await ac.get("/api/v1/equipos/mis-equipos")
        assert res_b.status_code == 200
        data_b = res_b.json()
        # Should return exactly 1 assignment, belonging to User B
        assert len(data_b) == 1
        assert data_b[0]["usuario_id"] == str(user_b_id)

    app.dependency_overrides.clear()
