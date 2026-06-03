from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, and_
from app.repositories.base import BaseRepository
from app.models.calificacion import Calificacion

class CalificacionRepository(BaseRepository[Calificacion]):
    def __init__(self, session, tenant_id: UUID):
        super().__init__(Calificacion, session, tenant_id)

    async def get_calificacion(
        self,
        entrada_padron_id: UUID,
        materia_id: UUID,
        docente_id: UUID,
        actividad: str
    ) -> Optional[Calificacion]:
        """
        Retrieves a single active grade by student entry, subject, teacher, and activity.
        """
        query = select(self.model).where(
            self.model.entrada_padron_id == entrada_padron_id,
            self.model.materia_id == materia_id,
            self.model.docente_id == docente_id,
            self.model.actividad == actividad
        )
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def vaciar_calificaciones(
        self,
        materia_id: UUID,
        docente_id: UUID
    ) -> int:
        """
        Logically deletes (soft delete) all grades imported by a specific teacher for a specific subject.
        Returns the number of rows updated.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == self.tenant_id,
                self.model.materia_id == materia_id,
                self.model.docente_id == docente_id,
                self.model.deleted_at.is_(None)
            )
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def bulk_upsert_calificaciones(
        self,
        materia_id: UUID,
        docente_id: UUID,
        calificaciones_data: List[dict]
    ) -> int:
        """
        Inserts or updates grade records in bulk. 
        Updates existing grades matching (entrada_padron_id, materia_id, docente_id, actividad).
        """
        count = 0
        for data in calificaciones_data:
            existing = await self.get_calificacion(
                entrada_padron_id=data['entrada_padron_id'],
                materia_id=materia_id,
                docente_id=docente_id,
                actividad=data['actividad']
            )

            if existing:
                existing.nota_numerica = data.get('nota_numerica')
                existing.nota_textual = data.get('nota_textual')
                existing.aprobado = data['aprobado']
                existing.finalizado = data.get('finalizado', True)
                existing.es_numerica = data.get('es_numerica', True)
                existing.origen = data.get('origen', 'Importado')
                existing.importado_at = data.get('importado_at', datetime.utcnow())
                existing.updated_at = datetime.utcnow()
            else:
                new_calif = Calificacion(
                    tenant_id=self.tenant_id,
                    entrada_padron_id=data['entrada_padron_id'],
                    materia_id=materia_id,
                    docente_id=docente_id,
                    actividad=data['actividad'],
                    nota_numerica=data.get('nota_numerica'),
                    nota_textual=data.get('nota_textual'),
                    aprobado=data['aprobado'],
                    finalizado=data.get('finalizado', True),
                    es_numerica=data.get('es_numerica', True),
                    origen=data.get('origen', 'Importado'),
                    importado_at=data.get('importado_at', datetime.utcnow())
                )
                self.session.add(new_calif)
            count += 1
        
        await self.session.flush()
        return count

    async def get_calificaciones_by_materia(
        self,
        materia_id: UUID,
        docente_id: Optional[UUID] = None
    ) -> List[Calificacion]:
        """
        Retrieves all active grades for a subject. Option to filter by docente_id.
        """
        query = select(self.model).where(self.model.materia_id == materia_id)
        if docente_id:
            query = query.where(self.model.docente_id == docente_id)
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_distinct_activities(
        self,
        materia_id: UUID,
        docente_id: Optional[UUID] = None
    ) -> List[str]:
        """
        Retrieves unique active activity names for a subject, optionally filtered by teacher.
        """
        query = select(self.model.actividad).where(self.model.materia_id == materia_id)
        if docente_id:
            query = query.where(self.model.docente_id == docente_id)
        query = self._apply_tenant_scope(query)
        query = query.distinct()
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_ungraded_textual_calificaciones(
        self,
        materia_id: UUID,
        docente_id: Optional[UUID] = None
    ) -> List[Calificacion]:
        """
        Gets all qualifications where finalizado == True, nota_numerica is null,
        nota_textual is null, and es_numerica == False (ungraded TPs).
        """
        query = select(self.model).where(
            self.model.materia_id == materia_id,
            self.model.finalizado == True,
            self.model.nota_numerica.is_(None),
            self.model.nota_textual.is_(None),
            self.model.es_numerica == False
        )
        if docente_id:
            query = query.where(self.model.docente_id == docente_id)
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

