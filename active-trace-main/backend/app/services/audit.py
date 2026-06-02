from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository

class AuditService:
    """
    Servicio de Auditoría para registrar acciones significativas en el sistema.
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = AuditLogRepository(AuditLog, db, tenant_id)

    async def log_action(
        self,
        actor_id: UUID,
        accion: str,
        impersonado_id: Optional[UUID] = None,
        materia_id: Optional[UUID] = None,
        detalle: Optional[Dict[str, Any]] = None,
        filas_afectadas: Optional[int] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Registra una acción en el log de auditoría.
        """
        log = AuditLog(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            accion=accion,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            ip=ip,
            user_agent=user_agent
        )
        # Usamos el repositorio para crear y persistir el registro
        await self.repo.create(log)
        await self.db.flush()
        return log
