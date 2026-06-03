from uuid import UUID
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.base import BaseRepository


class ComunicacionRepository(BaseRepository[Comunicacion]):
    """Repository for Comunicacion model with tenant-scoped and cross-tenant methods."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Comunicacion, session, tenant_id)

    async def list_by_lote(self, lote_id: UUID) -> list[Comunicacion]:
        """Tenant-scoped. Returns all comunicaciones for a given lote_id."""
        q = select(self.model).where(self.model.lote_id == lote_id)
        q = self._apply_tenant_scope(q)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def list_by_estado_sistema(self, estado: EstadoComunicacion) -> list[Comunicacion]:
        """SYSTEM-LEVEL — cross-tenant. Used by worker crash recovery only. No tenant scope.
        Returns all non-deleted comunicaciones in the given estado across all tenants."""
        q = select(self.model).where(
            and_(
                self.model.estado == estado,
                self.model.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def list_dispatchable(self) -> list[Comunicacion]:
        """SYSTEM-LEVEL — cross-tenant. Returns PENDIENTE + aprobado=True + not deleted rows.
        Used by the worker poll loop only. No tenant scope applied intentionally."""
        q = select(self.model).where(
            and_(
                self.model.estado == EstadoComunicacion.PENDIENTE,
                self.model.aprobado.is_(True),
                self.model.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def list_filtered(
        self,
        estado: EstadoComunicacion | None = None,
        lote_id: UUID | None = None,
        enviado_por: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Comunicacion]:
        """Tenant-scoped, paginated filter. All filters are optional."""
        q = select(self.model)
        if estado is not None:
            q = q.where(self.model.estado == estado)
        if lote_id is not None:
            q = q.where(self.model.lote_id == lote_id)
        if enviado_por is not None:
            q = q.where(self.model.enviado_por == enviado_por)
        q = self._apply_tenant_scope(q).offset(skip).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def lote_resumen(self, lote_id: UUID) -> dict[str, int]:
        """Aggregate by estado for a lote (tenant-scoped). Returns {estado_value: count}."""
        q = (
            select(self.model.estado, func.count())
            .where(self.model.lote_id == lote_id)
            .group_by(self.model.estado)
        )
        q = self._apply_tenant_scope(q)
        result = await self.session.execute(q)
        return {estado.value: count for estado, count in result.all()}

    async def bulk_approve_lote(self, lote_id: UUID) -> int:
        """Flip aprobado=True only on PENDIENTE rows that are not already approved.
        Returns count of newly approved rows. Flushes but does not commit."""
        rows = await self.list_by_lote(lote_id)
        count = 0
        for row in rows:
            if row.estado == EstadoComunicacion.PENDIENTE and not row.aprobado:
                row.aprobado = True
                count += 1
        if count:
            await self.session.flush()
        return count

    async def bulk_cancel_lote(self, lote_id: UUID) -> int:
        """Transition PENDIENTE rows to CANCELADO. Returns count of cancelled rows.
        Flushes but does not commit."""
        rows = await self.list_by_lote(lote_id)
        count = 0
        for row in rows:
            if row.estado == EstadoComunicacion.PENDIENTE:
                row.estado = EstadoComunicacion.CANCELADO
                count += 1
        if count:
            await self.session.flush()
        return count
