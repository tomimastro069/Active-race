from sqlalchemy import Column, String, Boolean, Float, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampedTenant

class Calificacion(Base, TimestampedTenant):
    """
    Entidad Calificación (E7).
    Almacena las calificaciones de los estudiantes en actividades.
    """
    __tablename__ = 'calificacion'

    entrada_padron_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('entrada_padron.id', ondelete='CASCADE'),
        nullable=False,
        doc="Relación con la entrada de padrón del alumno."
    )

    materia_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('materias.id', ondelete='CASCADE'),
        nullable=False,
        doc="Relación con la Materia."
    )

    docente_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete='CASCADE'),
        nullable=False,
        doc="Relación con el docente que importó la calificación."
    )

    actividad = Column(
        String(255),
        nullable=False,
        doc="Nombre de la actividad o tarea."
    )

    nota_numerica = Column(
        Float,
        nullable=True,
        doc="Nota numérica de la calificación."
    )

    nota_textual = Column(
        String(100),
        nullable=True,
        doc="Nota textual o cualitativa de la calificación."
    )

    aprobado = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="Indica si la calificación es aprobatoria."
    )

    finalizado = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Indica si la actividad está finalizada."
    )

    es_numerica = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Indica si la calificación es numérica o cualitativa."
    )

    origen = Column(
        String(50),
        nullable=False,
        default="Importado",
        doc="Origen de la calificación: Importado | Manual"
    )

    importado_at = Column(
        DateTime,
        nullable=True,
        doc="Fecha y hora de importación."
    )

    entrada_padron = relationship("EntradaPadron")
    materia = relationship("Materia")
    docente = relationship("Usuario")

    __table_args__ = (
        Index('idx_calificacion_lookup', 'tenant_id', 'entrada_padron_id', 'materia_id'),
        Index('idx_calificacion_docente', 'tenant_id', 'docente_id', 'materia_id'),
    )

    def __repr__(self):
        return f"<Calificacion(id={self.id!r}, entrada_padron_id={self.entrada_padron_id!r}, materia_id={self.materia_id!r}, aprobado={self.aprobado!r})>"
