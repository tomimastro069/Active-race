from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from app.repositories.base import BaseRepository
from app.models.guardia import Guardia
from app.models.asignacion import Asignacion

class GuardiaRepository(BaseRepository[Guardia]):
    def __init__(self, session, tenant_id: UUID):
        super().__init__(Guardia, session, tenant_id)

    async def list_by_materia(self, materia_id: UUID) -> List[Guardia]:
        query = select(self.model).where(self.model.materia_id == materia_id)
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_by_tutor(self, tutor_id: UUID) -> List[Guardia]:
        # Join with Asignacion to filter by user/tutor
        query = select(self.model).join(Asignacion, self.model.asignacion_id == Asignacion.id).where(
            Asignacion.usuario_id == tutor_id
        )
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()
