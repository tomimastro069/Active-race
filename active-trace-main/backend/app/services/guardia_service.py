from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia, EstadoGuardiaEnum
from app.repositories.guardia_repository import GuardiaRepository
from app.schemas.guardia import GuardiaCreate
from app.services.audit import AuditService

class GuardiaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = GuardiaRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    async def registrar_guardia(self, schema: GuardiaCreate, actor_id: UUID) -> Guardia:
        guardia = Guardia(
            materia_id=schema.materia_id,
            asignacion_id=schema.asignacion_id,
            dia_semana=schema.dia_semana,
            hora_inicio=schema.hora_inicio,
            hora_fin=schema.hora_fin,
            estado=EstadoGuardiaEnum.PENDIENTE
        )
        guardia = await self.repo.create(guardia)
        await self.db.flush()

        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="GUARDIA_REGISTRAR",
            materia_id=schema.materia_id,
            detalle={
                "guardia_id": str(guardia.id),
                "dia_semana": guardia.dia_semana,
                "hora_inicio": guardia.hora_inicio.isoformat(),
                "hora_fin": guardia.hora_fin.isoformat()
            }
        )
        return guardia

    async def aprobar_guardia(self, guardia_id: UUID, actor_id: UUID) -> Guardia:
        guardia = await self.repo.get_by_id(guardia_id)
        if not guardia:
            raise ValueError("La guardia no existe o pertenece a otro tenant.")

        if guardia.estado != EstadoGuardiaEnum.PENDIENTE:
            raise ValueError(f"No se puede aprobar una guardia en estado {guardia.estado}.")

        guardia.estado = EstadoGuardiaEnum.APROBADA
        guardia = await self.repo.update(guardia)
        await self.db.flush()

        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="GUARDIA_APROBAR",
            materia_id=guardia.materia_id,
            detalle={
                "guardia_id": str(guardia.id),
                "estado_nuevo": guardia.estado
            }
        )
        return guardia
