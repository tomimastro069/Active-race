from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.tarea import Tarea, ComentarioTarea
from app.repositories.base import BaseRepository

class TareaRepository(BaseRepository[Tarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Tarea, session, tenant_id)
        
    async def get_by_asignado(self, usuario_id: UUID, skip: int = 0, limit: int = 100) -> List[Tarea]:
        """Obtener tareas donde el usuario está involucrado (asignado o creador)."""
        query = select(self.model).where(
            (self.model.asignado_a == usuario_id) | (self.model.asignado_por == usuario_id)
        ).offset(skip).limit(limit)
        
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()

class ComentarioTareaRepository(BaseRepository[ComentarioTarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(ComentarioTarea, session, tenant_id)
        
    async def get_by_tarea(self, tarea_id: UUID) -> List[ComentarioTarea]:
        query = select(self.model).where(self.model.tarea_id == tarea_id).order_by(self.model.created_at.asc())
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()
