from sqlalchemy import Column, String
from app.models.base import Base, TimestampedTenant

class Rol(Base, TimestampedTenant):
    """
    Catálogo de Roles del sistema.
    tenant_id es nullable para permitir roles por defecto del sistema (globales).
    """
    __tablename__ = 'rol'

    nombre = Column(
        String(100),
        nullable=False,
        doc="Nombre único del rol (e.g. ADMIN, PROFESOR)."
    )

    descripcion = Column(
        String(255),
        nullable=True,
        doc="Descripción detallada de la función del rol."
    )

    def __repr__(self):
        return f"<Rol(id={self.id!r}, nombre={self.nombre!r})>"
