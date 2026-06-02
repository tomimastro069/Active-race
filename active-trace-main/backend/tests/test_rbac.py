import pytest
import uuid
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient
from fastapi import APIRouter, Depends, status

from app.main import app
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.models.asignacion import Asignacion
from app.repositories.rol import RolRepository
from app.repositories.permiso import PermisoRepository
from app.repositories.asignacion import AsignacionRepository
from app.core.dependencies import get_db, require_permission, get_current_user
from app.schemas.auth import CurrentUser

# Create a test router to verify require_permission guard
test_router = APIRouter(prefix="/test-rbac")

@test_router.get("/global", dependencies=[Depends(require_permission("avisos:publicar"))])
async def global_endpoint():
    return {"status": "authorized"}

@test_router.get("/propio", dependencies=[Depends(require_permission("atrasados:ver"))])
async def propio_endpoint():
    return {"status": "authorized_or_propio"}

app.include_router(test_router)


@pytest.mark.asyncio
async def test_rbac_database_models_and_repository(db_session):
    # Setup testing data
    tenant_id = uuid.uuid4()
    
    # 1. Create a tenant-specific Rol
    rol = Rol(tenant_id=tenant_id, nombre="TEST_ROLE", descripcion="Test description")
    db_session.add(rol)
    
    # 2. Create a Permiso
    permiso = Permiso(tenant_id=tenant_id, nombre="test:action", descripcion="Test permission")
    db_session.add(permiso)
    await db_session.flush()
    
    # 3. Associate Permiso to Rol
    rp = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    
    # 4. Create a User
    user = Usuario(tenant_id=tenant_id, email="rbac_user@example.com", hashed_password="hashed_pass")
    db_session.add(user)
    await db_session.flush()
    
    # 5. Create an active Assignment
    asignacion = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user.id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=1),
        hasta=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(asignacion)
    await db_session.commit()
    
    # Verify effective permissions
    repo = AsignacionRepository(Asignacion, db_session, tenant_id)
    perms = await repo.get_effective_permissions(user.id)
    assert "test:action" in perms
    
    roles = await repo.get_active_roles(user.id)
    assert "TEST_ROLE" in roles


@pytest.mark.asyncio
async def test_rbac_expired_and_deleted_assignments(db_session):
    tenant_id = uuid.uuid4()
    
    rol = Rol(tenant_id=tenant_id, nombre="EXPIRED_ROLE")
    permiso = Permiso(tenant_id=tenant_id, nombre="expired:action")
    db_session.add_all([rol, permiso])
    await db_session.flush()
    
    rp = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    
    user = Usuario(tenant_id=tenant_id, email="expired_user@example.com", hashed_password="hashed_pass")
    db_session.add(user)
    await db_session.flush()
    
    # Assignment already expired
    asignacion = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user.id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=5),
        hasta=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(asignacion)
    await db_session.commit()
    
    repo = AsignacionRepository(Asignacion, db_session, tenant_id)
    perms = await repo.get_effective_permissions(user.id)
    # Expired assignment should not yield permissions
    assert "expired:action" not in perms
    
    roles = await repo.get_active_roles(user.id)
    assert "EXPIRED_ROLE" not in roles


@pytest.mark.asyncio
async def test_rbac_guard_allow_and_block(db_session):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Mock get_current_user to return a CurrentUser
    mock_current_user = CurrentUser(
        id=user_id,
        tenant_id=tenant_id,
        email="test_guard@example.com",
        roles=["COORDINADOR"]
    )
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db] = lambda: db_session

    # We manually seed the database session with a role/permissions for this user to test require_permission
    rol = Rol(id=uuid.uuid4(), tenant_id=tenant_id, nombre="COORDINADOR")
    permiso_global = Permiso(id=uuid.uuid4(), tenant_id=tenant_id, nombre="avisos:publicar")
    permiso_propio = Permiso(id=uuid.uuid4(), tenant_id=tenant_id, nombre="atrasados:ver_propio")
    
    db_session.add_all([rol, permiso_global, permiso_propio])
    await db_session.flush()
    
    rp1 = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=permiso_global.id)
    rp2 = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=permiso_propio.id)
    
    # We must seed a user record first because of FK constraints in Asignacion
    user = Usuario(id=user_id, tenant_id=tenant_id, email="test_guard@example.com", hashed_password="pass")
    db_session.add(user)
    await db_session.flush()

    asignacion = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user_id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=1),
        hasta=None
    )
    db_session.add_all([rp1, rp2, asignacion])
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Access global endpoint with direct permission (avisos:publicar) -> Should allow
        res1 = await ac.get("/test-rbac/global")
        assert res1.status_code == 200
        assert res1.json() == {"status": "authorized"}

        # 2. Access endpoint requiring 'atrasados:ver', user has 'atrasados:ver_propio' -> Should allow (contextual pass)
        res2 = await ac.get("/test-rbac/propio")
        assert res2.status_code == 200
        assert res2.json() == {"status": "authorized_or_propio"}

        # 3. Simulate user with no assignments (mock a different user ID)
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            email="stranger@example.com",
            roles=[]
        )
        res3 = await ac.get("/test-rbac/global")
        assert res3.status_code == 403

    app.dependency_overrides.clear()
