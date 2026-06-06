import pytest
from datetime import time, datetime
from uuid import uuid4
from app.services.guardia_service import GuardiaService
from app.models.guardia import Guardia, EstadoGuardiaEnum
from app.models.materia import Materia
from app.models.asignacion import Asignacion
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.schemas.guardia import GuardiaCreate

@pytest.mark.asyncio
async def test_registrar_guardia(db_session):
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    await db_session.flush()

    materia = Materia(tenant_id=tenant.id, codigo="MAT1", nombre="Materia 1")
    user = Usuario(tenant_id=tenant.id, email="tutor@example.com", hashed_password="hashed_password")
    rol = Rol(tenant_id=tenant.id, nombre="TUTOR")
    db_session.add_all([materia, user, rol])
    await db_session.flush()

    asignacion = Asignacion(
        tenant_id=tenant.id,
        usuario_id=user.id,
        rol_id=rol.id,
        materia_id=materia.id,
        desde=datetime(2026, 6, 1)
    )
    db_session.add(asignacion)
    await db_session.flush()

    service = GuardiaService(db_session, tenant.id)

    payload = GuardiaCreate(
        materia_id=materia.id,
        asignacion_id=asignacion.id,
        dia_semana="Martes",
        hora_inicio=time(14, 0),
        hora_fin=time(14, 45)
    )

    actor_id = user.id
    guardia = await service.registrar_guardia(payload, actor_id=actor_id)

    assert guardia.id is not None
    assert guardia.estado == EstadoGuardiaEnum.PENDIENTE
    assert guardia.dia_semana == "Martes"
