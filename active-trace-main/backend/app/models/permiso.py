from sqlalchemy import Column, String
from app.models.base import Base, TimestampedTenant

class Permiso(Base, TimestampedTenant):
    """
    Catálogo de Permisos atómicos del sistema.
    Estructura 'modulo:accion' (e.g. calificaciones:importar).
    tenant_id es nullable para permitir permisos globales por defecto.
    """
    __tablename__ = 'permiso'

    nombre = Column(
        String(100),
        nullable=False,
        doc="Nombre único de la capacidad (e.g. calificaciones:importar)."
    )

    descripcion = Column(
        String(255),
        nullable=True,
        doc="Descripción de qué capacidad de negocio otorga el permiso."
    )

    def __repr__(self):
        return f"<Permiso(id={self.id!r}, nombre={self.nombre!r})>"
