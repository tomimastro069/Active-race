import pytest
from uuid import uuid4
from datetime import date, time, datetime
from sqlalchemy import select
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, DiaSemanaEnum, EstadoEncuentroEnum
from app.models.materia import Materia
from app.models.tenant import Tenant

@pytest.mark.asyncio
async def test_create_slot_and_instancias(db_session):
    # Setup Tenant and Materia
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    await db_session.flush()

    materia = Materia(tenant_id=tenant.id, codigo="MAT1", nombre="Materia 1")
    db_session.add(materia)
    await db_session.flush()

    # Create SlotEncuentro
    slot = SlotEncuentro(
        tenant_id=tenant.id,
        materia_id=materia.id,
        titulo="Clase de Consulta",
        hora=time(18, 0),
        dia_semana=DiaSemanaEnum.LUNES,
        fecha_inicio=date(2026, 6, 8),
        cant_semanas=4,
        meet_url="https://meet.google.com/abc-defg-hij"
    )
    db_session.add(slot)
    await db_session.flush()

    assert slot.id is not None
    assert slot.titulo == "Clase de Consulta"

    # Create InstanciaEncuentro
    instancia = InstanciaEncuentro(
        tenant_id=tenant.id,
        slot_id=slot.id,
        materia_id=materia.id,
        titulo="Clase de Consulta - Semana 1",
        fecha_hora=datetime(2026, 6, 8, 18, 0),
        estado=EstadoEncuentroEnum.PROGRAMADO,
        meet_url="https://meet.google.com/abc-defg-hij"
    )
    db_session.add(instancia)
    await db_session.flush()

    assert instancia.id is not None
    assert instancia.slot_id == slot.id
    assert instancia.estado == EstadoEncuentroEnum.PROGRAMADO
