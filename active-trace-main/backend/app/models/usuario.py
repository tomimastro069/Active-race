from sqlalchemy import Column, String, Boolean, Index, UniqueConstraint
from app.models.base import Base, TimestampedTenant

class Usuario(Base, TimestampedTenant):
    """
    Entidad Usuario (E4).
    En C-03 solo creamos el esqueleto para autenticación.
    En C-07 se agregarán los campos PII (DNI, CUIL, etc).
    """
    __tablename__ = 'usuario'

    email = Column(
        String(255),
        nullable=False,
        doc="Email del usuario. Cifrado en reposo en fase C-07, pero único por tenant."
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Contraseña hasheada con Argon2id."
    )

    estado = Column(
        String(50),
        default="Activo",
        nullable=False,
        doc="Estado: Activo | Inactivo"
    )

    two_factor_secret = Column(
        String(255),
        nullable=True,
        doc="Secreto base32 para TOTP 2FA. Se encriptará en producción."
    )

    two_factor_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Indica si el segundo factor está habilitado."
    )

    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_usuario_tenant_email'),
        Index('idx_usuario_tenant_email', 'tenant_id', 'email'),
    )

    def __repr__(self):
        return f"<Usuario(id={self.id!r}, email={self.email!r})>"
