from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampedTenant

class EvaluacionTipoEnum(str, enum.Enum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"

class EstadoReservaEnum(str, enum.Enum):
    ACTIVA = "Activa"
    CANCELADA = "Cancelada"

class Evaluacion(Base, TimestampedTenant):
    __tablename__ = "evaluaciones"

    materia_id = Column(UUID(as_uuid=True), ForeignKey("materias.id", ondelete="CASCADE"), nullable=False)
    cohorte_id = Column(UUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(Enum(EvaluacionTipoEnum, name="evaluacion_tipo_enum"), nullable=False)
    instancia = Column(String(255), nullable=False)
    titulo = Column(String(255), nullable=True)
    fecha = Column(Date, nullable=True)
    dias_disponibles = Column(Integer, nullable=False, default=1)
    cupos_totales = Column(Integer, nullable=False, default=10)

    # Relationships
    materia = relationship("Materia")
    cohorte = relationship("Cohorte")
    reservas = relationship("ReservaEvaluacion", back_populates="evaluacion", cascade="all, delete-orphan")
    resultados = relationship("ResultadoEvaluacion", back_populates="evaluacion", cascade="all, delete-orphan")
    convocados = relationship("ConvocadoEvaluacion", back_populates="evaluacion", cascade="all, delete-orphan")

class ReservaEvaluacion(Base, TimestampedTenant):
    __tablename__ = "reservas_evaluacion"

    evaluacion_id = Column(UUID(as_uuid=True), ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False)
    alumno_id = Column(UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), nullable=False)
    estado = Column(Enum(EstadoReservaEnum, name="estado_reserva_enum"), nullable=False, default=EstadoReservaEnum.ACTIVA)

    __table_args__ = (
        UniqueConstraint('evaluacion_id', 'alumno_id', name='uq_reserva_alumno_evaluacion'),
    )

    # Relationships
    evaluacion = relationship("Evaluacion", back_populates="reservas")
    alumno = relationship("Usuario")

class ResultadoEvaluacion(Base, TimestampedTenant):
    __tablename__ = "resultados_evaluacion"

    evaluacion_id = Column(UUID(as_uuid=True), ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False)
    alumno_id = Column(UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    nota_final = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint('evaluacion_id', 'alumno_id', name='uq_resultado_alumno_evaluacion'),
    )

    # Relationships
    evaluacion = relationship("Evaluacion", back_populates="resultados")
    alumno = relationship("Usuario")

class ConvocadoEvaluacion(Base, TimestampedTenant):
    """Alumno elegible (convocado) para una instancia de evaluación/coloquio.

    Es el padrón de coloquio (HU-30), separado del padrón general: define a
    quiénes corresponde convocar antes de que reserven cupo.
    """
    __tablename__ = "convocados_evaluacion"

    evaluacion_id = Column(UUID(as_uuid=True), ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False)
    alumno_id = Column(UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint('evaluacion_id', 'alumno_id', name='uq_convocado_alumno_evaluacion'),
    )

    # Relationships
    evaluacion = relationship("Evaluacion", back_populates="convocados")
    alumno = relationship("Usuario")
