from typing import List, Optional
from uuid import UUID
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.programa import ProgramaMateria


class ProgramaRepository(BaseRepository[ProgramaMateria]):
    def __init__(self, session, tenant_id: UUID):
        super().__init__(ProgramaMateria, session, tenant_id)

    async def list_programas(
        self,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
    ) -> List[ProgramaMateria]:
        """Lista programas activos del tenant, filtrable por materia/carrera/cohorte."""
        query = select(self.model)
        if materia_id is not None:
            query = query.where(self.model.materia_id == materia_id)
        if carrera_id is not None:
            query = query.where(self.model.carrera_id == carrera_id)
        if cohorte_id is not None:
            query = query.where(self.model.cohorte_id == cohorte_id)
        query = self._apply_tenant_scope(query).order_by(self.model.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
