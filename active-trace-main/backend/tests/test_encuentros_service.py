import pytest
from datetime import date, time, datetime, timedelta
from uuid import uuid4
from sqlalchemy import select
from app.services.encuentro_service import EncuentroService
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, DiaSemanaEnum, EstadoEncuentroEnum
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.schemas.encuentro import SlotEncuentroCreate, InstanciaEncuentroUpdate

@pytest.mark.asyncio
async def test_crear_recurrencia_y_generar_instancias(db_session):
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    await db_session.flush()

    materia = Materia(tenant_id=tenant.id, codigo="MAT1", nombre="Materia 1")
    db_session.add(materia)
    await db_session.flush()

    service = EncuentroService(db_session, tenant.id)

    # Monday is Lunes. Let's start on Monday, June 8, 2026.
    payload = SlotEncuentroCreate(
        materia_id=materia.id,
        titulo="Clase de Consulta",
        hora=time(18, 0),
        dia_semana=DiaSemanaEnum.LUNES,
        fecha_inicio=date(2026, 6, 8),
        cant_semanas=4,
        meet_url="https://meet.google.com/abc-defg-hij"
    )

    user = Usuario(tenant_id=tenant.id, email="profesor@example.com", hashed_password="hashed_password")
    db_session.add(user)
    await db_session.flush()

    actor_id = user.id
    slot, instancias = await service.crear_encuentro_recurrente(payload, actor_id=actor_id)

    assert slot.id is not None
    assert len(instancias) == 4
    
    # Check dates are weekly Mondays
    assert instancias[0].fecha_hora == datetime(2026, 6, 8, 18, 0)
    assert instancias[1].fecha_hora == datetime(2026, 6, 15, 18, 0)
    assert instancias[2].fecha_hora == datetime(2026, 6, 22, 18, 0)
    assert instancias[3].fecha_hora == datetime(2026, 6, 29, 18, 0)

    for inst in instancias:
        assert inst.estado == EstadoEncuentroEnum.PROGRAMADO
        assert inst.slot_id == slot.id
        assert inst.materia_id == materia.id

@pytest.mark.asyncio
async def test_recurrencia_con_salto_de_mes_y_bisiesto(db_session):
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    await db_session.flush()

    materia = Materia(tenant_id=tenant.id, codigo="MAT1", nombre="Materia 1")
    db_session.add(materia)
    await db_session.flush()

    service = EncuentroService(db_session, tenant.id)

    # Leap Year: Feb 2028 has 29 days.
    # Feb 28, 2028 is a Monday. Let's create a 3-week slot starting then.
    payload = SlotEncuentroCreate(
        materia_id=materia.id,
        titulo="Clase Bisiesta",
        hora=time(9, 0),
        dia_semana=DiaSemanaEnum.LUNES,
        fecha_inicio=date(2028, 2, 28),
        cant_semanas=3,
        meet_url="https://meet.google.com/abc-defg-hij"
    )

    user = Usuario(tenant_id=tenant.id, email="profesor2@example.com", hashed_password="hashed_password")
    db_session.add(user)
    await db_session.flush()

    actor_id = user.id
    _, instancias = await service.crear_encuentro_recurrente(payload, actor_id=actor_id)

    assert len(instancias) == 3
    # Feb 28 (Mon) -> March 6 (Mon) -> March 13 (Mon)
    assert instancias[0].fecha_hora == datetime(2028, 2, 28, 9, 0)
    assert instancias[1].fecha_hora == datetime(2028, 3, 6, 9, 0)
    assert instancias[2].fecha_hora == datetime(2028, 3, 13, 9, 0)
