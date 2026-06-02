from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.models.base import Base, TimestampedTenant

class TokenRefresco(Base, TimestampedTenant):
    """
    Almacena los refresh tokens emitidos para soportar rotación y revocación segura.
    """
    __tablename__ = 'token_refresco'

    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete="CASCADE"),
        nullable=False
    )
    
    token = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True
    )

    expira_el = Column(
        DateTime,
        nullable=False
    )

    # Para invalidar toda la familia si se detecta reuso
    familia_id = Column(
        String(255),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index('idx_token_refresco_usuario', 'usuario_id'),
        Index('idx_token_refresco_familia', 'familia_id'),
    )

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expira_el
