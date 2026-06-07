import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.audit_log import AuditLog
from app.core.security import generate_email_hash
from sqlalchemy import select

@pytest.mark.asyncio
async def test_perfil_endpoints(db_session):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Seed Tenant and User in DB
    tenant = Tenant(id=tenant_id, name="Tenant Test")
    user = Usuario(
        id=user_id,
        tenant_id=tenant_id,
        email="user_perfil@example.com",
        email_hash=generate_email_hash("user_perfil@example.com"),
        hashed_password="pwd",
        nombre="Nombre Original",
        apellidos="Apellido Original",
        cuil="20-12345678-9",
        dni="12345678",
        cbu="1111111111111111111111",
        alias_cbu="mi.alias.original",
        banco="Banco Original",
        regional="Regional Original",
        modalidad_cobro="Cobro Original"
    )
    db_session.add_all([tenant, user])
    await db_session.commit()

    # Mock CurrentUser
    mock_user = CurrentUser(
        id=user_id,
        tenant_id=tenant_id,
        email="user_perfil@example.com",
        roles=["PROFESOR"]
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. GET own profile
        res_get = await ac.get("/api/v1/perfil/")
        assert res_get.status_code == 200
        data = res_get.json()
        assert data["email"] == "user_perfil@example.com"
        assert data["nombre"] == "Nombre Original"
        # Masked fields
        assert data["dni"] == "*****5678"
        assert data["cuil"] == "*****78-9"
        assert data["cbu"] == "*****1111"
        assert data["alias_cbu"] == "*****inal"

        # 2. PATCH own profile - success
        update_payload = {
            "nombre": "Nombre Modificado",
            "banco": "Banco Modificado",
            "email": "user_perfil_nuevo@example.com",
            "modalidad_cobro": "Cobro Modificado"
        }
        res_patch = await ac.patch("/api/v1/perfil/", json=update_payload)
        assert res_patch.status_code == 200
        patch_data = res_patch.json()
        assert patch_data["nombre"] == "Nombre Modificado"
        assert patch_data["banco"] == "Banco Modificado"
        assert patch_data["email"] == "user_perfil_nuevo@example.com"
        assert patch_data["modalidad_cobro"] == "Cobro Modificado"

        # Check in DB that changes were saved
        await db_session.refresh(user)
        assert user.nombre == "Nombre Modificado"
        assert user.banco == "Banco Modificado"
        assert user.email == "user_perfil_nuevo@example.com"
        assert user.modalidad_cobro == "Cobro Modificado"

        # Check Audit Log for modification
        query = select(AuditLog).where(AuditLog.actor_id == user_id, AuditLog.accion == "PERFIL_MODIFICAR")
        res_audit = await db_session.execute(query)
        audit = res_audit.scalars().first()
        assert audit is not None
        assert audit.detalle["nombre_nuevo"] == "Nombre Modificado"

        # 3. PATCH own profile - attempt to change CUIL (must fail)
        bad_payload = {
            "cuil": "30-99999999-9"
        }
        res_bad = await ac.patch("/api/v1/perfil/", json=bad_payload)
        assert res_bad.status_code == 400
        assert "CUIL" in res_bad.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_mensajeria_endpoints(db_session):
    tenant1_id = uuid.uuid4()
    tenant2_id = uuid.uuid4()
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    user_c_id = uuid.uuid4() # distinct tenant

    # Seed Tenants and Users
    t1 = Tenant(id=tenant1_id, name="Tenant 1")
    t2 = Tenant(id=tenant2_id, name="Tenant 2")
    user_a = Usuario(
        id=user_a_id,
        tenant_id=tenant1_id,
        email="user_a@example.com",
        email_hash=generate_email_hash("user_a@example.com"),
        hashed_password="pwd",
        nombre="User",
        apellidos="A"
    )
    user_b = Usuario(
        id=user_b_id,
        tenant_id=tenant1_id,
        email="user_b@example.com",
        email_hash=generate_email_hash("user_b@example.com"),
        hashed_password="pwd",
        nombre="User",
        apellidos="B"
    )
    user_c = Usuario(
        id=user_c_id,
        tenant_id=tenant2_id,
        email="user_c@example.com",
        email_hash=generate_email_hash("user_c@example.com"),
        hashed_password="pwd",
        nombre="User",
        apellidos="C"
    )
    db_session.add_all([t1, t2, user_a, user_b, user_c])
    await db_session.commit()

    # Mock CurrentUser as User A
    mock_user_a = CurrentUser(
        id=user_a_id,
        tenant_id=tenant1_id,
        email="user_a@example.com",
        roles=["PROFESOR"]
    )

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user_a

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. GET list of threads (initially empty)
        res_list = await ac.get("/api/v1/inbox/threads")
        assert res_list.status_code == 200
        assert res_list.json() == []

        # 2. POST create new thread with User B (same tenant)
        thread_payload = {
            "asunto": "Tema de Consulta",
            "destinatario_id": str(user_b_id),
            "mensaje": "Hola User B, esto es una prueba."
        }
        res_create = await ac.post("/api/v1/inbox/threads", json=thread_payload)
        assert res_create.status_code == 201
        thread_data = res_create.json()
        assert thread_data["asunto"] == "Tema de Consulta"
        assert len(thread_data["miembros"]) == 2
        assert user_a_id in [uuid.UUID(m) for m in thread_data["miembros"]]
        assert user_b_id in [uuid.UUID(m) for m in thread_data["miembros"]]
        assert len(thread_data["mensajes"]) == 1
        assert thread_data["mensajes"][0]["contenido"] == "Hola User B, esto es una prueba."
        assert thread_data["mensajes"][0]["remitente_nombre"] == "User A"

        thread_id = thread_data["id"]

        # Check Audit Log for thread creation
        query_t = select(AuditLog).where(AuditLog.actor_id == user_a_id, AuditLog.accion == "MENSAJERIA_HILO_CREAR")
        res_audit_t = await db_session.execute(query_t)
        assert res_audit_t.scalars().first() is not None

        # 3. POST create new thread with User C (different tenant) -> should fail (403)
        bad_thread_payload = {
            "asunto": "Consulta Cross-Tenant",
            "destinatario_id": str(user_c_id),
            "mensaje": "Intento de cruce"
        }
        res_bad_create = await ac.post("/api/v1/inbox/threads", json=bad_thread_payload)
        assert res_bad_create.status_code == 403

        # 4. GET view thread as member
        res_get_thread = await ac.get(f"/api/v1/inbox/thread/{thread_id}")
        assert res_get_thread.status_code == 200
        get_thread_data = res_get_thread.json()
        assert get_thread_data["asunto"] == "Tema de Consulta"

        # 5. POST reply to thread as member
        reply_payload = {
            "contenido": "Esta es mi respuesta."
        }
        res_reply = await ac.post(f"/api/v1/inbox/thread/{thread_id}/reply", json=reply_payload)
        assert res_reply.status_code == 201
        reply_data = res_reply.json()
        assert reply_data["contenido"] == "Esta es mi respuesta."
        assert reply_data["remitente_nombre"] == "User A"

        # Check Audit Log for reply
        query_r = select(AuditLog).where(AuditLog.actor_id == user_a_id, AuditLog.accion == "MENSAJERIA_MENSAJE_ENVIAR")
        res_audit_r = await db_session.execute(query_r)
        assert res_audit_r.scalars().first() is not None

    # 6. Test unauthorized access (User C tries to access User A's thread)
    mock_user_c = CurrentUser(
        id=user_c_id,
        tenant_id=tenant2_id,
        email="user_c@example.com",
        roles=["PROFESOR"]
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user_c

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Attempt to view thread -> 403
        res_unauth_view = await ac.get(f"/api/v1/inbox/thread/{thread_id}")
        assert res_unauth_view.status_code == 403

        # Attempt to reply to thread -> 403
        res_unauth_reply = await ac.post(f"/api/v1/inbox/thread/{thread_id}/reply", json={"contenido": "Intento"})
        assert res_unauth_reply.status_code == 403

    app.dependency_overrides.clear()
