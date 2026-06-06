import enum
from sqlalchemy import Column, String, ForeignKey, Time, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from app.models.base import Base, TimestampedTenant

class EstadoGuardiaEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"
    APROBADA = "Aprobada"
    CANCELADA = "Cancelada"

class Guardia(Base, TimestampedTenant):
    """
    Representa un bloque de guardia o disponibilidad para tutorías de acompañamiento estudiantil.
    """
    __tablename__ = "guardia"

    materia_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
        doc="Materia asociada a la guardia."
    )

    asignacion_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("asignacion.id", ondelete="CASCADE"),
        nullable=False,
        doc="Asignación del tutor asociado a la guardia."
    )

    dia_semana = Column(
        String(100),
        nullable=False,
        doc="Día de la semana de la guardia."
    )

    hora_inicio = Column(
        Time,
        nullable=False,
        doc="Hora de inicio de la guardia."
    )

    hora_fin = Column(
        Time,
        nullable=False,
        doc="Hora de finalización de la guardia."
    )

    estado = Column(
        SAEnum(EstadoGuardiaEnum, name="estadoguardiaenum"),
        nullable=False,
        default=EstadoGuardiaEnum.PENDIENTE,
        doc="Estado de la guardia."
    )

    def __repr__(self) -> str:
        return f"<Guardia(id={self.id!r}, asignacion_id={self.asignacion_id!r}, dia_semana={self.dia_semana!r}, estado={self.estado!r})>"
