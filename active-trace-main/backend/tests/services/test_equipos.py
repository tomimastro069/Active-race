import pytest
import uuid
from datetime import datetime, timedelta
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.asignacion import Asignacion
from app.services.usuario import UsuarioService
from app.services.equipos import EquiposService
from app.schemas.usuario import UsuarioCreate
from app.schemas.asignacion import AsignacionMasivaCreate, EquipoClonarRequest, AsignacionVigenciaUpdate
from app.core.security import generate_email_hash
from app.repositories.audit_log import AuditLogRepository
from app.models.audit_log import AuditLog

@pytest.mark.asyncio
async def test_asignacion_masiva_success(db_session):
    """Test successful mass assignment and audit log generation."""
    # Setup Tenant
    tenant = Tenant(name="Mass Assign Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    # Create actor
    actor = Usuario(
        tenant_id=tenant_id,
        email="actor_mass@example.com",
        email_hash=generate_email_hash("actor_mass@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(actor)
    await db_session.flush()

    # Create users to assign
    user1 = Usuario(
        tenant_id=tenant_id,
        email="user1@example.com",
        email_hash=generate_email_hash("user1@example.com"),
        hashed_password="pwd",
        estado="Activo",
        nombre="User",
        apellidos="One"
    )
    user2 = Usuario(
        tenant_id=tenant_id,
        email="user2@example.com",
        email_hash=generate_email_hash("user2@example.com"),
        hashed_password="pwd",
        estado="Activo",
        nombre="User",
        apellidos="Two"
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.flush()

    # Create Rol
    rol = Rol(tenant_id=tenant_id, nombre="PROFESOR", descripcion="Profesor")
    db_session.add(rol)
    await db_session.flush()

    service = EquiposService(db_session, tenant_id)

    # Execute mass assignment
    schema = AsignacionMasivaCreate(
        usuario_ids=[user1.id, user2.id],
        rol_id=rol.id,
        materia_id=uuid.uuid4(),
        cohorte_id=uuid.uuid4(),
        desde=datetime.utcnow() - timedelta(days=1),
        hasta=datetime.utcnow() + timedelta(days=1)
    )

    assignments = await service.asignacion_masiva(schema, actor_id=actor.id)
    assert len(assignments) == 2
    assert {a.usuario_id for a in assignments} == {user1.id, user2.id}
    assert all(a.rol_id == rol.id for a in assignments)
    assert all(a.estado_vigencia == "Vigente" for a in assignments)

    # Verify audit log is written
    audit_repo = AuditLogRepository(AuditLog, db_session, tenant_id)
    audit_logs = await audit_repo.list_all()
    assert len(audit_logs) >= 1
    mass_assign_log = [l for l in audit_logs if l.accion == "ASIGNACION_MASIVA"]
    assert len(mass_assign_log) == 1
    assert mass_assign_log[0].actor_id == actor.id
    assert mass_assign_log[0].filas_afectadas == 2


@pytest.mark.asyncio
async def test_asignacion_masiva_invalid_user_rollback(db_session):
    """Test that if a user in the mass assignment list is invalid, the entire operation rolls back."""
    # Setup Tenant
    tenant = Tenant(name="Mass Assign Rollback Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    # Create actor
    actor = Usuario(
        tenant_id=tenant_id,
        email="actor_mass_rollback@example.com",
        email_hash=generate_email_hash("actor_mass_rollback@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(actor)
    await db_session.flush()

    # Create one valid user
    user1 = Usuario(
        tenant_id=tenant_id,
        email="user_rollback@example.com",
        email_hash=generate_email_hash("user_rollback@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(user1)
    await db_session.flush()

    # Create Rol
    rol = Rol(tenant_id=tenant_id, nombre="PROFESOR", descripcion="Profesor")
    db_session.add(rol)
    await db_session.flush()

    service = EquiposService(db_session, tenant_id)

    # Try mass assignment with one valid and one random invalid user UUID
    schema = AsignacionMasivaCreate(
        usuario_ids=[user1.id, uuid.uuid4()],
        rol_id=rol.id,
        materia_id=uuid.uuid4(),
        cohorte_id=uuid.uuid4(),
        desde=datetime.utcnow()
    )

    with pytest.raises(ValueError) as exc:
        await service.asignacion_masiva(schema, actor_id=actor.id)
    assert "no existe o pertenece a otro tenant" in str(exc.value)

    # Verify no assignments were created for user1
    from sqlalchemy import select
    res = await db_session.execute(select(Asignacion).where(Asignacion.usuario_id == user1.id))
    assert len(res.scalars().all()) == 0


@pytest.mark.asyncio
async def test_clonar_equipo_success_and_conflict(db_session):
    """Test successful team cloning and validation when destination already has assignments."""
    # Setup Tenant
    tenant = Tenant(name="Cloning Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    # Create actor
    actor = Usuario(
        tenant_id=tenant_id,
        email="actor_clone@example.com",
        email_hash=generate_email_hash("actor_clone@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(actor)
    await db_session.flush()

    # Create a teacher
    teacher = Usuario(
        tenant_id=tenant_id,
        email="teacher_clone@example.com",
        email_hash=generate_email_hash("teacher_clone@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(teacher)
    await db_session.flush()

    # Create Rol
    rol = Rol(tenant_id=tenant_id, nombre="PROFESOR", descripcion="Profesor")
    db_session.add(rol)
    await db_session.flush()

    # Setup source and target context ids
    src_materia = uuid.uuid4()
    src_cohorte = uuid.uuid4()
    target_materia = uuid.uuid4()
    target_cohorte = uuid.uuid4()

    # Create active assignment in source context
    src_asig = Asignacion(
        tenant_id=tenant_id,
        usuario_id=teacher.id,
        rol_id=rol.id,
        materia_id=src_materia,
        cohorte_id=src_cohorte,
        desde=datetime.utcnow() - timedelta(days=2),
        hasta=datetime.utcnow() + timedelta(days=2)
    )
    db_session.add(src_asig)
    await db_session.flush()

    service = EquiposService(db_session, tenant_id)

    # 1. Successful Clone
    schema_clone = EquipoClonarRequest(
        source_materia_id=src_materia,
        source_cohorte_id=src_cohorte,
        target_materia_id=target_materia,
        target_cohorte_id=target_cohorte,
        nuevo_desde=datetime.utcnow(),
        nuevo_hasta=datetime.utcnow() + timedelta(days=5)
    )

    cloned = await service.clonar_equipo(schema_clone, actor_id=actor.id)
    assert len(cloned) == 1
    assert cloned[0].usuario_id == teacher.id
    assert cloned[0].materia_id == target_materia
    assert cloned[0].cohorte_id == target_cohorte

    # 2. Conflict: Target already has active assignments
    # Trying to clone again to target should fail
    with pytest.raises(ValueError) as exc:
        await service.clonar_equipo(schema_clone, actor_id=actor.id)
    assert "El contexto destino ya tiene asignaciones activas" in str(exc.value)


@pytest.mark.asyncio
async def test_modificar_vigencia_masiva_success(db_session):
    """Test modifying validity masively for a context."""
    # Setup Tenant
    tenant = Tenant(name="Vigencia Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    # Create actor
    actor = Usuario(
        tenant_id=tenant_id,
        email="actor_vig@example.com",
        email_hash=generate_email_hash("actor_vig@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(actor)
    await db_session.flush()

    # Create a teacher
    teacher = Usuario(
        tenant_id=tenant_id,
        email="teacher_vig@example.com",
        email_hash=generate_email_hash("teacher_vig@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(teacher)
    await db_session.flush()

    # Create Rol
    rol = Rol(tenant_id=tenant_id, nombre="PROFESOR", descripcion="Profesor")
    db_session.add(rol)
    await db_session.flush()

    materia_id = uuid.uuid4()
    cohorte_id = uuid.uuid4()

    asig = Asignacion(
        tenant_id=tenant_id,
        usuario_id=teacher.id,
        rol_id=rol.id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        desde=datetime.utcnow() - timedelta(days=2),
        hasta=datetime.utcnow() + timedelta(days=2)
    )
    db_session.add(asig)
    await db_session.flush()

    service = EquiposService(db_session, tenant_id)

    # Modify validity masively
    new_desde = datetime.utcnow() - timedelta(days=1)
    new_hasta = datetime.utcnow() + timedelta(days=10)
    schema_vig = AsignacionVigenciaUpdate(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        desde=new_desde,
        hasta=new_hasta
    )

    updated = await service.modificar_vigencia_masiva(schema_vig, actor_id=actor.id)
    assert len(updated) == 1
    assert updated[0].desde == new_desde
    assert updated[0].hasta == new_hasta


@pytest.mark.asyncio
async def test_exportar_equipo_csv(db_session):
    """Test that exportar_equipo generates a valid CSV of active assignments."""
    tenant = Tenant(name="Export Tenant")
    db_session.add(tenant)
    await db_session.flush()
    tenant_id = tenant.id

    teacher = Usuario(
        tenant_id=tenant_id,
        email="teacher_exp@example.com",
        email_hash=generate_email_hash("teacher_exp@example.com"),
        hashed_password="pwd",
        estado="Activo",
        nombre="José",
        apellidos="San Martín"
    )
    db_session.add(teacher)
    await db_session.flush()

    rol = Rol(tenant_id=tenant_id, nombre="PROFESOR", descripcion="Profesor")
    db_session.add(rol)
    await db_session.flush()

    materia_id = uuid.uuid4()

    asig = Asignacion(
        tenant_id=tenant_id,
        usuario_id=teacher.id,
        rol_id=rol.id,
        materia_id=materia_id,
        desde=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(asig)
    await db_session.flush()

    service = EquiposService(db_session, tenant_id)

    csv_content = await service.exportar_equipo(materia_id=materia_id)
    assert "Nombre,Apellidos,Email,Rol,Desde,Hasta,Comisiones,Responsable" in csv_content
    assert "José" in csv_content
    assert "San Martín" in csv_content
    assert "PROFESOR" in csv_content
