from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, and_
from app.repositories.base import BaseRepository
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro

class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    def __init__(self, session, tenant_id: UUID):
        super().__init__(SlotEncuentro, session, tenant_id)

    async def list_by_materia(self, materia_id: UUID) -> List[SlotEncuentro]:
        query = select(self.model).where(self.model.materia_id == materia_id)
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()

class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    def __init__(self, session, tenant_id: UUID):
        super().__init__(InstanciaEncuentro, session, tenant_id)

    async def list_by_materia(self, materia_id: UUID) -> List[InstanciaEncuentro]:
        query = select(self.model).where(self.model.materia_id == materia_id)
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_by_slot(self, slot_id: UUID) -> List[InstanciaEncuentro]:
        query = select(self.model).where(self.model.slot_id == slot_id)
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_by_date_range(self, desde: date, hasta: date) -> List[InstanciaEncuentro]:
        # filter instances by date (the date of fecha_hora field)
        query = select(self.model).where(
            and_(
                self.model.fecha_hora >= desde,
                self.model.fecha_hora <= hasta
            )
        )
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()
