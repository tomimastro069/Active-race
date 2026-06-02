from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Integer, JSON, ForeignKey, UUID as SQLAlchemyUUID
from app.models.base import Base

class AuditLog(Base):
    """
    Entidad Log de Auditoría (E-AUD).
    Registro inmutable (append-only) de toda acción significativa en el sistema.
    """
    __tablename__ = 'audit_log'

    id = Column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    tenant_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('tenant.id', ondelete='CASCADE'),
        nullable=False
    )

    fecha_hora = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    actor_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete='RESTRICT'),
        nullable=False
    )

    impersonado_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete='SET NULL'),
        nullable=True
    )

    materia_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        nullable=True  # No FK constraint yet because Materia is C-06
    )

    accion = Column(
        String(100),
        nullable=False
    )

    detalle = Column(
        JSON,
        nullable=True
    )

    filas_afectadas = Column(
        Integer,
        nullable=True
    )

    ip = Column(
        String(50),
        nullable=True
    )

    user_agent = Column(
        String(255),
        nullable=True
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id!r}, accion={self.accion!r}, actor_id={self.actor_id!r})>"
