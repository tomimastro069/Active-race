import pytest
from uuid import uuid4
from datetime import time, datetime
from app.repositories.guardia_repository import GuardiaRepository
from app.models.guardia import Guardia, EstadoGuardiaEnum
from app.models.materia import Materia
from app.models.asignacion import Asignacion
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.rol import Rol

@pytest.mark.asyncio
async def test_guardia_repository_isolation(db_session):
    # Setup Tenant A & B
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    materia_a = Materia(tenant_id=tenant_a.id, codigo="MAT_A", nombre="Materia A")
    materia_b = Materia(tenant_id=tenant_b.id, codigo="MAT_B", nombre="Materia B")
    user_a = Usuario(tenant_id=tenant_a.id, email="tutor_a@example.com", hashed_password="hashed_password")
    user_b = Usuario(tenant_id=tenant_b.id, email="tutor_b@example.com", hashed_password="hashed_password")
    rol = Rol(tenant_id=tenant_a.id, nombre="TUTOR")
    db_session.add_all([materia_a, materia_b, user_a, user_b, rol])
    await db_session.flush()

    asignacion_a = Asignacion(
        tenant_id=tenant_a.id,
        usuario_id=user_a.id,
        rol_id=rol.id,
        materia_id=materia_a.id,
        desde=datetime(2026, 6, 1)
    )
    asignacion_b = Asignacion(
        tenant_id=tenant_b.id,
        usuario_id=user_b.id,
        rol_id=rol.id,
        materia_id=materia_b.id,
        desde=datetime(2026, 6, 1)
    )
    db_session.add_all([asignacion_a, asignacion_b])
    await db_session.flush()

    guardia_a = Guardia(
        tenant_id=tenant_a.id,
        materia_id=materia_a.id,
        asignacion_id=asignacion_a.id,
        dia_semana="Martes",
        hora_inicio=time(14, 0),
        hora_fin=time(14, 45),
        estado=EstadoGuardiaEnum.PENDIENTE
    )
    guardia_b = Guardia(
        tenant_id=tenant_b.id,
        materia_id=materia_b.id,
        asignacion_id=asignacion_b.id,
        dia_semana="Miércoles",
        hora_inicio=time(14, 0),
        hora_fin=time(14, 45),
        estado=EstadoGuardiaEnum.PENDIENTE
    )
    db_session.add_all([guardia_a, guardia_b])
    await db_session.flush()

    repo_a = GuardiaRepository(db_session, tenant_a.id)
    repo_b = GuardiaRepository(db_session, tenant_b.id)

    guardias_a = await repo_a.list_all()
    assert len(guardias_a) == 1
    assert guardias_a[0].id == guardia_a.id

    guardias_b = await repo_b.list_all()
    assert len(guardias_b) == 1
    assert guardias_b[0].id == guardia_b.id
