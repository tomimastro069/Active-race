import pytest
from uuid import uuid4
from datetime import date, time, datetime
from app.repositories.encuentro_repository import SlotEncuentroRepository, InstanciaEncuentroRepository
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, DiaSemanaEnum, EstadoEncuentroEnum
from app.models.materia import Materia
from app.models.tenant import Tenant

@pytest.mark.asyncio
async def test_encuentro_repository_isolation(db_session):
    # Setup two tenants
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    materia_a = Materia(tenant_id=tenant_a.id, codigo="MAT_A", nombre="Materia A")
    materia_b = Materia(tenant_id=tenant_b.id, codigo="MAT_B", nombre="Materia B")
    db_session.add_all([materia_a, materia_b])
    await db_session.flush()

    # Create slot for Tenant A
    slot_a = SlotEncuentro(
        tenant_id=tenant_a.id,
        materia_id=materia_a.id,
        titulo="Clase A",
        hora=time(18, 0),
        dia_semana=DiaSemanaEnum.LUNES,
        fecha_inicio=date(2026, 6, 8),
        cant_semanas=4,
        meet_url="https://meet.google.com/a"
    )
    # Create slot for Tenant B
    slot_b = SlotEncuentro(
        tenant_id=tenant_b.id,
        materia_id=materia_b.id,
        titulo="Clase B",
        hora=time(18, 0),
        dia_semana=DiaSemanaEnum.LUNES,
        fecha_inicio=date(2026, 6, 8),
        cant_semanas=4,
        meet_url="https://meet.google.com/b"
    )
    db_session.add_all([slot_a, slot_b])
    await db_session.flush()

    # Repos for Tenant A
    repo_slot_a = SlotEncuentroRepository(db_session, tenant_a.id)
    repo_slot_b = SlotEncuentroRepository(db_session, tenant_b.id)

    # Verify list_all only lists tenant-scoped records
    slots_for_a = await repo_slot_a.list_all()
    assert len(slots_for_a) == 1
    assert slots_for_a[0].id == slot_a.id

    slots_for_b = await repo_slot_b.list_all()
    assert len(slots_for_b) == 1
    assert slots_for_b[0].id == slot_b.id
