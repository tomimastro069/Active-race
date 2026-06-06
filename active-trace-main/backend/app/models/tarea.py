import enum
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampedTenant, Base

class EstadoTareaEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"

class Tarea(Base, TimestampedTenant):
    __tablename__ = "tareas"
    
    materia_id = Column(UUID(as_uuid=True), nullable=True)
    asignado_a = Column(UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False)
    asignado_por = Column(UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False)
    estado = Column(Enum(EstadoTareaEnum), default=EstadoTareaEnum.PENDIENTE, nullable=False)
    descripcion = Column(String, nullable=False)
    contexto_id = Column(UUID(as_uuid=True), nullable=True)
    
    comentarios = relationship("ComentarioTarea", back_populates="tarea", cascade="all, delete-orphan")

class ComentarioTarea(Base, TimestampedTenant):
    __tablename__ = "comentarios_tarea"
    
    tarea_id = Column(UUID(as_uuid=True), ForeignKey("tareas.id"), nullable=False)
    autor_id = Column(UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False)
    texto = Column(String, nullable=False)
    
    tarea = relationship("Tarea", back_populates="comentarios")
