from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampedTenant

class Asignacion(Base, TimestampedTenant):
    """
    Entidad Asignación (E5).
    Vincula a un usuario con un rol dentro de un contexto académico concreto y rango de fechas.
    Es el eje central del modelo de autorización contextual.
    """
    __tablename__ = 'asignacion'

    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete="CASCADE"),
        nullable=False,
        doc="Usuario asignado."
    )

    rol_id = Column(
        UUID(as_uuid=True),
        ForeignKey('rol.id', ondelete="RESTRICT"),
        nullable=False,
        doc="Rol asignado."
    )

    materia_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID de la Materia. Nullable si el rol es global de tenant."
    )

    carrera_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID de la Carrera (opcional)."
    )

    cohorte_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID de la Cohorte (opcional)."
    )

    comisiones = Column(
        JSON,
        nullable=True,
        doc="Lista de nombres de comisiones asignadas (e.g. ['Comision A', 'Comision B'])."
    )

    responsable_id = Column(
        UUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete="SET_NULL"),
        nullable=True,
        doc="Usuario coordinador o supervisor responsable."
    )

    desde = Column(
        DateTime,
        nullable=False,
        doc="Inicio de la vigencia de la asignación."
    )

    hasta = Column(
        DateTime,
        nullable=True,
        doc="Fin de la vigencia de la asignación (nulo = abierta)."
    )

    def __repr__(self):
        return f"<Asignacion(id={self.id!r}, usuario_id={self.usuario_id!r}, rol_id={self.rol_id!r})>"
