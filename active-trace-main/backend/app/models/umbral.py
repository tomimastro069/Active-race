from sqlalchemy import Column, Integer, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampedTenant

class UmbralMateria(Base, TimestampedTenant):
    """
    Entidad UmbralMateria (E8).
    Define los umbrales de aprobación numéricos y cualitativos para una asignación de docente/materia.
    """
    __tablename__ = 'umbral_materia'

    asignacion_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('asignacion.id', ondelete='CASCADE'),
        nullable=False,
        doc="Relación con la Asignación del docente."
    )

    materia_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('materias.id', ondelete='CASCADE'),
        nullable=False,
        doc="Relación con la Materia."
    )

    umbral_pct = Column(
        Integer,
        default=60,
        nullable=False,
        doc="Porcentaje mínimo requerido para aprobar actividades numéricas (default 60%)."
    )

    valores_aprobatorios = Column(
        JSON,
        nullable=True,
        doc="Lista JSON de valores de notas textuales/cualitativas considerados como aprobados."
    )

    asignacion = relationship("Asignacion")
    materia = relationship("Materia")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'asignacion_id', 'materia_id', name='uix_umbral_tenant_asignacion_materia'),
        Index('idx_umbral_lookup', 'tenant_id', 'asignacion_id', 'materia_id'),
    )

    def __repr__(self):
        return f"<UmbralMateria(id={self.id!r}, asignacion_id={self.asignacion_id!r}, materia_id={self.materia_id!r}, umbral_pct={self.umbral_pct!r})>"
