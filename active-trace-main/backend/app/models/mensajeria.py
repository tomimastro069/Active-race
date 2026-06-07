from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Table, Index
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampedTenant

# Tabla de asociación muchos-a-muchos para los miembros de un hilo
thread_member = Table(
    'thread_member',
    Base.metadata,
    Column('thread_id', SQLAlchemyUUID(as_uuid=True), ForeignKey('thread.id', ondelete='CASCADE'), primary_key=True),
    Column('usuario_id', SQLAlchemyUUID(as_uuid=True), ForeignKey('usuario.id', ondelete='CASCADE'), primary_key=True)
)

class Thread(Base, TimestampedTenant):
    """
    Representa un hilo de conversación interno entre usuarios.
    """
    __tablename__ = 'thread'

    asunto = Column(
        String(255),
        nullable=False,
        doc="Asunto del hilo de conversación."
    )

    creador_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete='CASCADE'),
        nullable=False,
        doc="ID del usuario que inició el hilo."
    )

    is_closed = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Indica si el hilo está cerrado lógicamente."
    )

    # Relación con los mensajes en el hilo
    mensajes = relationship(
        "Message",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    # Relación con los usuarios miembros del hilo
    miembros = relationship(
        "Usuario",
        secondary=thread_member,
        doc="Usuarios que participan en el hilo."
    )

    __table_args__ = (
        Index('idx_thread_tenant_id', 'tenant_id'),
        Index('idx_thread_creador_id', 'creador_id'),
    )

    def __repr__(self) -> str:
        return f"<Thread(id={self.id!r}, asunto={self.asunto!r}, is_closed={self.is_closed!r})>"


class Message(Base, TimestampedTenant):
    """
    Representa un mensaje individual dentro de un hilo de conversación.
    """
    __tablename__ = 'message'

    thread_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('thread.id', ondelete='CASCADE'),
        nullable=False,
        doc="ID del hilo al que pertenece el mensaje."
    )

    remitente_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey('usuario.id', ondelete='CASCADE'),
        nullable=False,
        doc="ID del usuario que envió el mensaje."
    )

    contenido = Column(
        Text,
        nullable=False,
        doc="Contenido del mensaje en texto plano."
    )

    # Relación inversa al hilo
    thread = relationship(
        "Thread",
        back_populates="mensajes"
    )

    # Relación al remitente
    remitente = relationship(
        "Usuario",
        doc="Usuario remitente del mensaje."
    )

    __table_args__ = (
        Index('idx_message_tenant_id', 'tenant_id'),
        Index('idx_message_thread_id', 'thread_id'),
        Index('idx_message_remitente_id', 'remitente_id'),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id!r}, thread_id={self.thread_id!r}, remitente_id={self.remitente_id!r})>"
