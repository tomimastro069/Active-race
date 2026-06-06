import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Time, Date, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from app.models.base import Base, TimestampedTenant

class DiaSemanaEnum(str, enum.Enum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"

class EstadoEncuentroEnum(str, enum.Enum):
    PROGRAMADO = "Programado"
    REALIZADO = "Realizado"
    SUSPENDIDO = "Suspendido"

class SlotEncuentro(Base, TimestampedTenant):
    """
    Representa un slot recurrente de encuentro (clase sincrónica).
    """
    __tablename__ = "slot_encuentro"

    materia_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
        doc="Materia asociada al slot."
    )

    titulo = Column(
        String(255),
        nullable=False,
        doc="Título o descripción del slot de encuentro."
    )

    hora = Column(
        Time,
        nullable=False,
        doc="Hora de inicio del encuentro."
    )

    dia_semana = Column(
        SAEnum(DiaSemanaEnum, name="diasemanaenum"),
        nullable=False,
        doc="Día de la semana del encuentro."
    )

    fecha_inicio = Column(
        Date,
        nullable=False,
        doc="Fecha de inicio de la recurrencia."
    )

    cant_semanas = Column(
        Integer,
        nullable=False,
        doc="Cantidad de semanas de duración de la recurrencia."
    )

    meet_url = Column(
        String(500),
        nullable=False,
        doc="URL de la videollamada."
    )

    def __repr__(self) -> str:
        return f"<SlotEncuentro(id={self.id!r}, titulo={self.titulo!r}, cant_semanas={self.cant_semanas!r})>"

class InstanciaEncuentro(Base, TimestampedTenant):
    """
    Representa una instancia individual de un encuentro sincrónico (único o de un slot recurrente).
    """
    __tablename__ = "instancia_encuentro"

    slot_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("slot_encuentro.id", ondelete="SET NULL"),
        nullable=True,
        doc="Slot recurrente de donde proviene. Nulo para encuentros únicos."
    )

    materia_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
        doc="Materia asociada a la instancia."
    )

    titulo = Column(
        String(255),
        nullable=False,
        doc="Título específico de la instancia."
    )

    fecha_hora = Column(
        DateTime,
        nullable=False,
        doc="Fecha y hora de la instancia."
    )

    estado = Column(
        SAEnum(EstadoEncuentroEnum, name="estadoencuentroenum"),
        nullable=False,
        default=EstadoEncuentroEnum.PROGRAMADO,
        doc="Estado de la instancia."
    )

    meet_url = Column(
        String(500),
        nullable=True,
        doc="Enlace a la videoconferencia (copiado o personalizado)."
    )

    video_url = Column(
        String(500),
        nullable=True,
        doc="Enlace a la grabación del encuentro."
    )

    comentario = Column(
        Text,
        nullable=True,
        doc="Notas o comentarios post-clase."
    )

    def __repr__(self) -> str:
        return f"<InstanciaEncuentro(id={self.id!r}, titulo={self.titulo!r}, fecha_hora={self.fecha_hora!r}, estado={self.estado!r})>"
