from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampedTenant

class RolPermiso(Base, TimestampedTenant):
    """
    Tabla intermedia que asocia Roles con Permisos.
    Permite parametrizar dinámicamente qué permisos posee cada rol.
    """
    __tablename__ = 'rol_permiso'

    rol_id = Column(
        UUID(as_uuid=True),
        ForeignKey('rol.id', ondelete="CASCADE"),
        nullable=False,
        doc="Asociación al Rol."
    )

    permiso_id = Column(
        UUID(as_uuid=True),
        ForeignKey('permiso.id', ondelete="CASCADE"),
        nullable=False,
        doc="Asociación al Permiso."
    )

    def __repr__(self):
        return f"<RolPermiso(rol_id={self.rol_id!r}, permiso_id={self.permiso_id!r})>"
