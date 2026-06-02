import pytest
import uuid
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy import select

from app.main import app
from app.models.usuario import Usuario
from app.models.audit_log import AuditLog
from app.models.rol import Rol
from app.models.tenant import Tenant
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.models.asignacion import Asignacion
from app.repositories.audit_log import AuditLogRepository
from app.services.audit import AuditService

from app.core.security import create_access_token
from app.core.dependencies import get_current_user, get_db
from app.schemas.auth import CurrentUser

# Router test to verify audit contexts
test_router = APIRouter(prefix="/test-audit")

@test_router.post("/action")
async def perform_action(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db)
):
    audit_service = AuditService(db, current_user.tenant_id)
    # Atribución bajo impersonación: usar actor_id del request.state (real) e impersonado_id (suplantado)
    actor_id = getattr(request.state, "actor_id", current_user.id)
    impersonado_id = getattr(request.state, "impersonado_id", None)
    
    await audit_service.log_action(
        actor_id=actor_id,
        impersonado_id=impersonado_id,
        accion="CALIFICACIONES_IMPORTAR",
        ip=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent"),
        detalle={"msg": "Test import"}
    )
    return {"status": "ok"}

# Re-register test router to avoid duplicate route errors
for route in app.routes:
    if getattr(route, "path", None) == "/test-audit/action":
        app.routes.remove(route)
app.include_router(test_router)


@pytest.mark.asyncio
async def test_audit_log_model_and_append_only(db_session):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Tenant Test")
    actor = Usuario(id=actor_id, tenant_id=tenant_id, email="actor@example.com", hashed_password="hashed_pass")
    db_session.add_all([tenant, actor])
    await db_session.flush()
    
    # 1. Test model creation
    log = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        accion="TEST_ACTION",
        detalle={"info": "test"},
        ip="127.0.0.1",
        user_agent="pytest"
    )
    db_session.add(log)
    await db_session.commit()
    
    assert log.id is not None
    assert log.fecha_hora is not None
    
    # 2. Test Repository blocking operations
    repo = AuditLogRepository(AuditLog, db_session, tenant_id)
    
    with pytest.raises(NotImplementedError):
        await repo.update(log.id, accion="UPDATED_ACTION")
        
    with pytest.raises(NotImplementedError):
        await repo.delete(log.id)
        
    with pytest.raises(NotImplementedError):
        await repo.delete_logical(log.id)


@pytest.mark.asyncio
async def test_impersonation_jwt_claims():
    actor_id = uuid.uuid4()
    impersonated_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    
    token = create_access_token(
        data={"sub": str(actor_id), "tenant_id": str(tenant_id), "roles": ["ADMIN"]},
        impersonated_sub=str(impersonated_id)
    )
    assert token is not None


@pytest.mark.asyncio
async def test_impersonation_flow(db_session):
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Tenant Test")
    db_session.add(tenant)
    await db_session.flush()
    
    # Create two users: Admin and Target
    admin = Usuario(id=uuid.uuid4(), tenant_id=tenant_id, email="admin@example.com", hashed_password="hashed_pass")
    target = Usuario(id=uuid.uuid4(), tenant_id=tenant_id, email="target@example.com", hashed_password="hashed_pass")
    db_session.add_all([admin, target])
    await db_session.commit()
    
    # Generate token for admin impersonating target
    token = create_access_token(
        data={"sub": str(admin.id), "tenant_id": str(tenant_id), "roles": ["ADMIN"]},
        impersonated_sub=str(target.id)
    )
    
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Make request with this token to /test-audit/action
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {token}", "User-Agent": "pytest-impersonate"}
        res = await ac.post("/test-audit/action", headers=headers)
        assert res.status_code == 200
        
    # Verify AuditLog has recorded the action with actor_id = admin.id and impersonado_id = target.id
    result = await db_session.execute(
        select(AuditLog).filter_by(accion="CALIFICACIONES_IMPORTAR").order_by(AuditLog.fecha_hora.desc())
    )
    import_log = result.scalars().first()
    assert import_log is not None
    assert import_log.actor_id == admin.id
    assert import_log.impersonado_id == target.id
    assert import_log.user_agent == "pytest-impersonate"
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_impersonate_endpoint_authorized(db_session):
    tenant_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    target_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Tenant Test")
    db_session.add(tenant)
    await db_session.flush()
    
    # Setup users
    admin = Usuario(id=admin_id, tenant_id=tenant_id, email="superadmin@example.com", hashed_password="hashed_pass")
    target = Usuario(id=target_id, tenant_id=tenant_id, email="target_user@example.com", hashed_password="hashed_pass")
    
    # Setup RBAC: admin must have "impersonacion:usar"
    rol = Rol(id=uuid.uuid4(), tenant_id=tenant_id, nombre="ADMIN")
    permiso = Permiso(id=uuid.uuid4(), tenant_id=tenant_id, nombre="impersonacion:usar")
    
    db_session.add_all([admin, target, rol, permiso])
    await db_session.flush()
    
    rp = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=permiso.id)
    asignacion = Asignacion(
        tenant_id=tenant_id,
        usuario_id=admin_id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=1),
        hasta=None
    )
    db_session.add_all([rp, asignacion])
    await db_session.commit()
    
    # Mock current user for the REST request
    mock_current_user = CurrentUser(
        id=admin_id,
        tenant_id=tenant_id,
        email="superadmin@example.com",
        roles=["ADMIN"]
    )
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Call the endpoint POST /api/v1/auth/impersonate
        res = await ac.post("/api/v1/auth/impersonate", json={"usuario_id": str(target_id)})
        assert res.status_code == 200
        token_data = res.json()
        assert "access_token" in token_data
        
    # Verify IMPERSONACION_INICIAR log
    result = await db_session.execute(
        select(AuditLog).filter_by(accion="IMPERSONACION_INICIAR").order_by(AuditLog.fecha_hora.desc())
    )
    audit_log = result.scalars().first()
    assert audit_log is not None
    assert audit_log.actor_id == admin_id
    assert audit_log.impersonado_id == target_id
    
    app.dependency_overrides.clear()
