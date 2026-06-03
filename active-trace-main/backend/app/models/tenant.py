from uuid import UUID
from sqlalchemy import Boolean, Column, String, Index, UniqueConstraint
from sqlalchemy.orm import declared_attr
from app.models.base import Base, TimestampedTenant


class Tenant(Base, TimestampedTenant):
    """
    Root entity for multi-tenant isolation.
    
    Each institution is a separate Tenant. All data in the system
    carries tenant_id and filters by tenant by default (row-level isolation).
    
    The Tenant model itself is special: its own tenant_id is NULL (it's the root).
    """
    
    __tablename__ = 'tenant'
    
    name = Column(
        String(255),
        nullable=False,
        doc="Institution name (e.g., 'Universidad Nacional')"
    )

    aprobacion_comunicaciones_masivas = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc="Cuando es True, los envios masivos (lote > 1) requieren aprobacion explicita antes de ser despachados.",
    )

    __table_args__ = (
        UniqueConstraint('name', name='uq_tenant_name'),
        Index('idx_tenant_created_at', 'created_at'),
        Index('idx_tenant_deleted_at', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id!r}, name={self.name!r})>"
