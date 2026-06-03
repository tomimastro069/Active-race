import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID

from app.core.types import EncryptedString
from app.models.base import Base, TimestampedTenant


class EstadoComunicacion(str, enum.Enum):
    PENDIENTE = "Pendiente"
    ENVIANDO = "Enviando"
    ENVIADO = "Enviado"
    ERROR = "Error"
    CANCELADO = "Cancelado"


class Comunicacion(Base, TimestampedTenant):
    """
    Registro de una comunicacion saliente (email) hacia un destinatario.

    Ciclo de vida: Pendiente -> Enviando -> Enviado | Error | Cancelado.
    El campo `destinatario` esta cifrado con AES-256 — NUNCA debe ser logueado
    ni incluido en representaciones textuales del objeto.
    """

    __tablename__ = "comunicacion"

    enviado_por = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        doc="Usuario (JWT) que origino el envio. Nunca proviene del body.",
    )

    materia_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="CASCADE"),  # tabla plural — critico
        nullable=False,
        doc="Materia a la que esta asociada la comunicacion.",
    )

    destinatario = Column(
        EncryptedString,
        nullable=False,
        doc="Email del destinatario cifrado en AES-256. NUNCA loguear.",
    )

    destinatario_hash = Column(
        String(64),
        nullable=False,
        index=True,
        doc="HMAC-SHA256 del email para busquedas sin exponer PII.",
    )

    asunto = Column(
        String(500),
        nullable=False,
        doc="Asunto del email ya renderizado.",
    )

    cuerpo = Column(
        Text,
        nullable=False,
        doc="Cuerpo del email ya renderizado.",
    )

    estado = Column(
        SAEnum(EstadoComunicacion, name="estadocomunicacion"),
        nullable=False,
        default=EstadoComunicacion.PENDIENTE,
        doc="Estado de la maquina de estados del envio.",
    )

    lote_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        nullable=True,
        doc="Identificador del lote para envios masivos. NULL para envios individuales.",
    )

    aprobado = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="Indica si el envio fue aprobado. Ortogonal al estado del ciclo de vida.",
    )

    enviado_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp del envio exitoso. NULL si aun no fue enviado.",
    )

    intentos = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Cantidad de intentos de envio realizados.",
    )

    max_intentos = Column(
        Integer,
        nullable=False,
        default=3,
        doc="Maximo de reintentos permitidos antes de pasar a ERROR.",
    )

    __table_args__ = (
        Index("idx_comunicacion_tenant_estado", "tenant_id", "estado"),
        Index("idx_comunicacion_lote_id", "lote_id"),
        Index("idx_comunicacion_tenant_enviado_por", "tenant_id", "enviado_por"),
        Index("idx_comunicacion_destinatario_hash", "destinatario_hash"),
    )

    def __repr__(self) -> str:
        # NUNCA incluir `destinatario` en repr — es PII cifrada
        return (
            f"<Comunicacion(id={self.id!r}, "
            f"estado={self.estado!r}, "
            f"hash={self.destinatario_hash!r})>"
        )
