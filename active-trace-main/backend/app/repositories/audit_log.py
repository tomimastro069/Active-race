from typing import List
from uuid import UUID
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.audit_log import AuditLog

class AuditLogRepository(BaseRepository[AuditLog]):
    """
    Repositorio para AuditLog (E-AUD).
    Sobrescribe métodos de mutación para asegurar el comportamiento append-only.
    """

    def _apply_tenant_scope(self, query):
        """
        Aplica filtro de tenant_id sin deleted_at, ya que AuditLog no tiene soft-delete.
        """
        if self.tenant_id is None:
            raise ValueError(
                "tenant_id is None. Cannot execute query without tenant scope."
            )
        return query.where(self.model.tenant_id == self.tenant_id)

    async def update(self, *args, **kwargs):
        """Bloquea actualizaciones."""
        raise NotImplementedError("Los registros de auditoría son append-only.")

    async def delete(self, *args, **kwargs):
        """Bloquea eliminaciones físicas."""
        raise NotImplementedError("No se pueden eliminar registros de auditoría.")

    async def delete_logical(self, *args, **kwargs):
        """Bloquea eliminaciones lógicas."""
        raise NotImplementedError("No se pueden aplicar soft-deletes a la auditoría.")

    async def get_all(self) -> List[AuditLog]:
        """
        Obtiene todos los logs de auditoría para el tenant.
        """
        query = select(self.model)
        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().all()
