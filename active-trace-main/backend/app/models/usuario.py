from sqlalchemy import Column, String, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import validates
from app.models.base import Base, TimestampedTenant
from app.core.types import EncryptedString

class Usuario(Base, TimestampedTenant):
    """
    Entidad Usuario (E4).
    En C-03 solo creamos el esqueleto para autenticación.
    En C-07 se agregarán los campos PII (DNI, CUIL, etc).
    """
    __tablename__ = 'usuario'

    email = Column(
        EncryptedString(255),
        nullable=False,
        doc="Email del usuario. Cifrado en reposo."
    )

    email_hash = Column(
        String(64),
        nullable=False,
        doc="Hash determinista del email (HMAC-SHA256) para búsquedas rápidas y unicidad."
    )

    @validates("email")
    def validate_email(self, key, value):
        from app.core.security import generate_email_hash
        self.email_hash = generate_email_hash(value)
        return value


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

    nombre = Column(
        String(100),
        nullable=True,
        doc="Nombre del usuario."
    )

    apellidos = Column(
        String(100),
        nullable=True,
        doc="Apellidos del usuario."
    )

    dni = Column(
        EncryptedString(255),
        nullable=True,
        doc="Documento Nacional de Identidad. Cifrado."
    )

    cuil = Column(
        EncryptedString(255),
        nullable=True,
        doc="Código Único de Identificación Laboral. Cifrado."
    )

    cbu = Column(
        EncryptedString(255),
        nullable=True,
        doc="Clave Bancaria Uniforme. Cifrado."
    )

    alias_cbu = Column(
        EncryptedString(255),
        nullable=True,
        doc="Alias de CBU. Cifrado."
    )

    banco = Column(
        String(100),
        nullable=True,
        doc="Banco asociado del usuario."
    )

    regional = Column(
        String(100),
        nullable=True,
        doc="Regional o sede del usuario."
    )

    legajo = Column(
        String(50),
        nullable=True,
        doc="Legajo del usuario (atributo de negocio, opcional)."
    )

    legajo_profesional = Column(
        String(50),
        nullable=True,
        doc="Legajo profesional del usuario (opcional)."
    )

    facturador = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Indica si el usuario emite facturas."
    )

    modalidad_cobro = Column(
        String(100),
        nullable=True,
        doc="Modalidad de cobro del usuario."
    )

    __table_args__ = (
        UniqueConstraint('tenant_id', 'email_hash', name='uq_usuario_tenant_email'),
        Index('idx_usuario_tenant_email', 'tenant_id', 'email_hash'),
    )

    def __repr__(self):
        return f"<Usuario(id={self.id!r}, email_hash={self.email_hash!r})>"

