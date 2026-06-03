import pytest
import uuid
from datetime import datetime, timedelta
from app.models.usuario import Usuario
from app.models.asignacion import Asignacion
from app.models.rol import Rol
from app.core.security import generate_email_hash, decrypt_attr

@pytest.mark.asyncio
async def test_usuario_encrypted_string_fields(db_session):
    """Test that sensitive fields in Usuario are stored encrypted and decrypted on read."""
    tenant_id = uuid.uuid4()
    email_val = "sensitive_user@example.com"
    email_h = generate_email_hash(email_val)
    
    user = Usuario(
        tenant_id=tenant_id,
        email=email_val,
        email_hash=email_h,
        hashed_password="hashedpassword123",
        nombre="Juan",
        apellidos="Pérez",
        dni="12345678",
        cuil="20-12345678-9",
        cbu="0170000000000000000000",
        alias_cbu="juan.perez.cbu",
        banco="Banco de la Nación Argentina",
        regional="Buenos Aires",
        legajo="LEG-999",
        legajo_profesional="PROF-888",
        facturador=True
    )
    
    db_session.add(user)
    await db_session.flush()
    user_id = user.id

    # Evict or refresh from session to force database reload
    db_session.expire_all()

    # Query user back
    result = await db_session.get(Usuario, user_id)
    assert result is not None
    assert result.email == email_val
    assert result.dni == "12345678"
    assert result.cuil == "20-12345678-9"
    assert result.cbu == "0170000000000000000000"
    assert result.alias_cbu == "juan.perez.cbu"
    assert result.nombre == "Juan"
    assert result.apellidos == "Pérez"
    assert result.banco == "Banco de la Nación Argentina"
    assert result.regional == "Buenos Aires"
    assert result.legajo == "LEG-999"
    assert result.legajo_profesional == "PROF-888"
    assert result.facturador is True

    # Verify that the value in the database is actually encrypted
    # We can do this by executing a raw SQL query
    import sqlalchemy as sa
    raw_result = (await db_session.execute(
        sa.text(f"SELECT email, dni, cuil, cbu, alias_cbu FROM usuario WHERE id = '{user_id}'")
    )).fetchone()

    
    db_email, db_dni, db_cuil, db_cbu, db_alias_cbu = raw_result
    
    # Assert they are different from plaintext
    assert db_email != email_val
    assert db_dni != "12345678"
    assert db_cuil != "20-12345678-9"
    assert db_cbu != "0170000000000000000000"
    assert db_alias_cbu != "juan.perez.cbu"
    
    # Assert they decrypt correctly
    assert decrypt_attr(db_email) == email_val
    assert decrypt_attr(db_dni) == "12345678"

@pytest.mark.asyncio
async def test_asignacion_estado_vigencia(db_session):
    """Test the dynamic estado_vigencia property calculation."""
    tenant_id = uuid.uuid4()
    
    # 1. Create a dummy User and Role
    user = Usuario(
        tenant_id=tenant_id,
        email="test_asig@example.com",
        email_hash=generate_email_hash("test_asig@example.com"),
        hashed_password="pwd",
        estado="Activo"
    )
    db_session.add(user)
    await db_session.flush()

    rol = Rol(
        tenant_id=tenant_id,
        nombre="TUTOR_TEST",
        descripcion="Test Role"
    )
    db_session.add(rol)
    await db_session.flush()

    # 2. Asignación vigente (sin fecha hasta)
    asig_vigente_open = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user.id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=1),
        hasta=None
    )
    assert asig_vigente_open.estado_vigencia == "Vigente"

    # 3. Asignación vigente (con fecha hasta en el futuro)
    asig_vigente_future = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user.id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=1),
        hasta=datetime.utcnow() + timedelta(days=1)
    )
    assert asig_vigente_future.estado_vigencia == "Vigente"

    # 4. Asignación vencida (hasta en el pasado)
    asig_vencida = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user.id,
        rol_id=rol.id,
        desde=datetime.utcnow() - timedelta(days=5),
        hasta=datetime.utcnow() - timedelta(days=1)
    )
    assert asig_vencida.estado_vigencia == "Vencida"

    # 5. Asignación futura (desde en el futuro)
    asig_futura = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user.id,
        rol_id=rol.id,
        desde=datetime.utcnow() + timedelta(days=1),
        hasta=datetime.utcnow() + timedelta(days=5)
    )
    assert asig_futura.estado_vigencia == "Vencida"
