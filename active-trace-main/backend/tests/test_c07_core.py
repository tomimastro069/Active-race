from typing import List
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app.models.usuario import Usuario
from app.models.asignacion import Asignacion
from app.models.rol import Rol
from app.models.tenant import Tenant
from app.repositories.usuario import UsuarioRepository
from app.services.usuario import UsuarioService
from app.services.asignacion import AsignacionService
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.schemas.asignacion import AsignacionCreate, AsignacionUpdate
from app.core.security import generate_email_hash

@pytest.mark.asyncio
async def test_email_hash_uniqueness_same_tenant(db_session):
    """Test that two users with the same email cannot exist in the same tenant (DB constraint)."""
    tenant = Tenant(name="Uniqueness Same Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    email_val = "duplicate@example.com"
    email_h = generate_email_hash(email_val)

    user1 = Usuario(
        tenant_id=tenant_id,
        email=email_val,
        email_hash=email_h,
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(user1)
    await db_session.flush()

    user2 = Usuario(
        tenant_id=tenant_id,
        email=email_val,
        email_hash=email_h,
        hashed_password="pwd2",
        estado="Activo"
    )
    db_session.add(user2)
    
    with pytest.raises(IntegrityError):
        await db_session.flush()

@pytest.mark.asyncio
async def test_email_hash_uniqueness_different_tenants(db_session):
    """Test that two users with the same email CAN exist in different tenants."""
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    db_session.add(tenant_a)
    db_session.add(tenant_b)
    await db_session.flush()

    email_val = "shared@example.com"
    email_h = generate_email_hash(email_val)

    user_a = Usuario(
        tenant_id=tenant_a.id,
        email=email_val,
        email_hash=email_h,
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(user_a)
    await db_session.flush()

    user_b = Usuario(
        tenant_id=tenant_b.id,
        email=email_val,
        email_hash=email_h,
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(user_b)
    
    # Should not raise any integrity error
    await db_session.flush()

@pytest.mark.asyncio
async def test_usuario_service_crud(db_session):
    """Test full CRUD operations via UsuarioService including auditing."""
    tenant = Tenant(name="CRUD Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    # Create actor user
    actor_user = Usuario(
        tenant_id=tenant_id,
        email="actor@example.com",
        email_hash=generate_email_hash("actor@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(actor_user)
    await db_session.flush()
    actor_id = actor_user.id

    service = UsuarioService(db_session, tenant_id)

    # 1. Create
    schema_create = UsuarioCreate(
        email="juan.perez@example.com",
        password="mysecretpassword",
        nombre="Juan",
        apellidos="Pérez",
        dni="99998888",
        facturador=True
    )
    user = await service.create_usuario(schema_create, actor_id=actor_id)
    assert user.id is not None
    assert user.email == "juan.perez@example.com"
    assert user.nombre == "Juan"
    assert user.facturador is True

    # 2. Get and Response mapping (verifying PII masking)
    db_user = await service.get_usuario(user.id)
    assert db_user is not None
    
    # Masked representation
    resp = service.to_response(db_user, mask_pii=True)
    assert resp.email == "juan.perez@example.com"
    assert resp.nombre == "Juan"
    assert resp.dni == "*****8888"  # Masked!
    assert resp.facturador is True

    # Unmasked representation
    resp_unmasked = service.to_response(db_user, mask_pii=False)
    assert resp_unmasked.dni == "99998888"

    # 3. Update
    schema_update = UsuarioUpdate(
        nombre="Juan Carlos",
        dni="11112222"
    )
    updated_user = await service.update_usuario(user.id, schema_update, actor_id=actor_id)
    assert updated_user.nombre == "Juan Carlos"
    assert updated_user.dni == "11112222"

    # Verify duplicate email raises ValueError in service
    with pytest.raises(ValueError) as exc:
        schema_dup = UsuarioCreate(
            email="juan.perez@example.com",
            password="otherpwd"
        )
        await service.create_usuario(schema_dup, actor_id=actor_id)
    assert "Ya existe un usuario con el email" in str(exc.value)

@pytest.mark.asyncio
async def test_asignacion_service_validations(db_session):
    """Test date ranges and related entities validations in AsignacionService."""
    tenant = Tenant(name="Asig Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    # Create actor user
    actor_user = Usuario(
        tenant_id=tenant_id,
        email="actor_asig@example.com",
        email_hash=generate_email_hash("actor_asig@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(actor_user)
    await db_session.flush()
    actor_id = actor_user.id
    
    user_service = UsuarioService(db_session, tenant_id)
    asig_service = AsignacionService(db_session, tenant_id)

    # 1. Create a User and a Rol
    user_schema = UsuarioCreate(email="docente@example.com", password="password")
    user = await user_service.create_usuario(user_schema, actor_id=actor_id)

    rol = Rol(tenant_id=tenant_id, nombre="PROFESOR", descripcion="Profesor universitario")
    db_session.add(rol)
    await db_session.flush()

    # 2. Try creating assignment with invalid user
    with pytest.raises(ValueError) as exc:
        schema_bad_user = AsignacionCreate(
            usuario_id=uuid.uuid4(),
            rol_id=rol.id,
            desde=datetime.utcnow()
        )
        await asig_service.create_assignment(schema_bad_user, actor_id=actor_id)
    assert "El usuario asignado no existe" in str(exc.value)

    # 3. Try creating assignment with invalid dates (desde > hasta)
    with pytest.raises(ValueError) as exc:
        schema_bad_dates = AsignacionCreate(
            usuario_id=user.id,
            rol_id=rol.id,
            desde=datetime.utcnow() + timedelta(days=5),
            hasta=datetime.utcnow() + timedelta(days=2)
        )
        await asig_service.create_assignment(schema_bad_dates, actor_id=actor_id)
    assert "La fecha de inicio 'desde' no puede ser posterior" in str(exc.value)

    # 4. Create valid assignment
    schema_ok = AsignacionCreate(
        usuario_id=user.id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=1),
        hasta=datetime.utcnow() + timedelta(days=5)
    )
    asig = await asig_service.create_assignment(schema_ok, actor_id=actor_id)
    assert asig.id is not None
    assert asig.estado_vigencia == "Vigente"

    # 5. List and Update
    lst = await asig_service.list_assignments(usuario_id=user.id)
    assert len(lst) == 1
    assert lst[0].id == asig.id

    schema_update = AsignacionUpdate(
        hasta=datetime.utcnow() - timedelta(minutes=1)  # Force expiration
    )
    updated = await asig_service.update_assignment(asig.id, schema_update, actor_id=actor_id)
    assert updated.estado_vigencia == "Vencida"

    # 6. Delete
    await asig_service.delete_assignment(asig.id, actor_id=actor_id)
    deleted = await asig_service.get_assignment(asig.id)
    assert deleted is None  # Excluded by tenant scope / soft delete

