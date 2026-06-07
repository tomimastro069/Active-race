from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.mensajeria import Thread, Message
from app.models.usuario import Usuario
from app.repositories.mensajeria import MensajeriaRepository
from app.repositories.usuario import UsuarioRepository
from app.services.audit import AuditService
from app.schemas.mensajeria import MessageResponse, ThreadResponse

class MensajeriaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = MensajeriaRepository(Thread, db, tenant_id)
        self.usuario_repo = UsuarioRepository(Usuario, db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    def message_to_response(self, msg: Message) -> MessageResponse:
        nombre = msg.remitente.nombre or ""
        apellidos = msg.remitente.apellidos or ""
        full_name = f"{nombre} {apellidos}".strip() or msg.remitente.email
        return MessageResponse(
            id=msg.id,
            thread_id=msg.thread_id,
            remitente_id=msg.remitente_id,
            remitente_nombre=full_name,
            contenido=msg.contenido,
            created_at=msg.created_at
        )

    def thread_to_response(self, thread: Thread) -> ThreadResponse:
        mensajes_response = []
        if thread.mensajes:
            mensajes_response = [self.message_to_response(m) for m in thread.mensajes]
        return ThreadResponse(
            id=thread.id,
            tenant_id=thread.tenant_id,
            asunto=thread.asunto,
            creador_id=thread.creador_id,
            is_closed=thread.is_closed,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            miembros=[m.id for m in thread.miembros],
            mensajes=mensajes_response
        )

    async def create_thread(self, creador_id: UUID, asunto: str, destinatario_id: UUID, mensaje_contenido: str) -> Thread:
        """
        Crea un nuevo hilo de conversación y el primer mensaje.
        Ambos miembros deben pertenecer al mismo tenant.
        """
        # Obtener destinatario (UsuarioRepository filtra automáticamente por tenant_id)
        destinatario = await self.usuario_repo.get_by_id(destinatario_id)
        if not destinatario:
            raise PermissionError("Acceso denegado: el destinatario no existe o pertenece a otro tenant.")

        creador = await self.usuario_repo.get_by_id(creador_id)
        if not creador:
            raise PermissionError("Acceso denegado: el creador no existe.")

        # Crear el hilo
        thread = Thread(
            asunto=asunto,
            creador_id=creador_id,
            is_closed=False
        )
        # Agregar miembros (creador y destinatario)
        thread.miembros.append(creador)
        # Si el destinatario es el mismo creador, evitamos duplicarlo en la lista
        if creador_id != destinatario_id:
            thread.miembros.append(destinatario)

        thread = await self.repo.create(thread)

        # Crear primer mensaje
        first_message = Message(
            thread_id=thread.id,
            remitente_id=creador_id,
            contenido=mensaje_contenido
        )
        await self.repo.save_message(first_message)

        # Loguear en auditoría
        await self.audit_service.log_action(
            actor_id=creador_id,
            accion="MENSAJERIA_HILO_CREAR",
            detalle={"thread_id": str(thread.id), "asunto": asunto}
        )

        return thread

    async def reply_to_thread(self, thread_id: UUID, remitente_id: UUID, contenido: str) -> Message:
        """
        Agrega una respuesta a un hilo existente.
        Verifica que el remitente sea miembro del hilo.
        """
        thread = await self.repo.get_thread_by_id_and_member(thread_id, remitente_id)
        if not thread:
            raise PermissionError("Acceso denegado: no es miembro del hilo o este no existe.")

        if thread.is_closed:
            raise ValueError("No se puede responder a un hilo cerrado.")

        # Crear mensaje
        message = Message(
            thread_id=thread_id,
            remitente_id=remitente_id,
            contenido=contenido
        )
        message = await self.repo.save_message(message)

        # Actualizar timestamp del hilo para ordenación
        from datetime import datetime
        thread.updated_at = datetime.utcnow()
        await self.repo.update(thread)

        # Loguear en auditoría
        await self.audit_service.log_action(
            actor_id=remitente_id,
            accion="MENSAJERIA_MENSAJE_ENVIAR",
            detalle={"thread_id": str(thread_id), "message_id": str(message.id)}
        )

        return message

    async def list_threads(self, usuario_id: UUID) -> List[Thread]:
        """
        Lista los hilos en los que participa el usuario.
        """
        return await self.repo.get_threads_by_member(usuario_id)

    async def get_thread(self, thread_id: UUID, usuario_id: UUID) -> Thread:
        """
        Obtiene los detalles de un hilo y sus mensajes si el usuario es miembro.
        """
        thread = await self.repo.get_thread_by_id_and_member(thread_id, usuario_id)
        if not thread:
            raise PermissionError("Acceso denegado: no es miembro del hilo o este no existe.")
        return thread
