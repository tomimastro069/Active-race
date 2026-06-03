from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from app.repositories.base import BaseRepository
from app.models.umbral import UmbralMateria

class UmbralMateriaRepository(BaseRepository[UmbralMateria]):
    def __init__(self, session, tenant_id: UUID):
        super().__init__(UmbralMateria, session, tenant_id)

    async def get_by_asignacion_y_materia(
        self,
        asignacion_id: UUID,
        materia_id: UUID
    ) -> Optional[UmbralMateria]:
        """
        Retrieves the threshold configuration for a specific assignment and subject.
        """
        query = select(self.model).where(
            self.model.asignacion_id == asignacion_id,
            self.model.materia_id == materia_id
        )
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def upsert_umbral(
        self,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: Optional[list] = None
    ) -> UmbralMateria:
        """
        Creates or updates the threshold configuration for an assignment and subject.
        """
        existing = await self.get_by_asignacion_y_materia(asignacion_id, materia_id)
        if existing:
            existing.umbral_pct = umbral_pct
            existing.valores_aprobatorios = valores_aprobatorios
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            new_umbral = UmbralMateria(
                tenant_id=self.tenant_id,
                asignacion_id=asignacion_id,
                materia_id=materia_id,
                umbral_pct=umbral_pct,
                valores_aprobatorios=valores_aprobatorios
            )
            self.session.add(new_umbral)
            await self.session.flush()
            return new_umbral
