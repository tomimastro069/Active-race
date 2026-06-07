from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.mensajeria import Thread, Message

class MensajeriaRepository(BaseRepository[Thread]):
    async def get_threads_by_member(self, usuario_id: UUID) -> List[Thread]:
        """
        Retorna todos los hilos donde el usuario es miembro, ordenados por fecha de actualización desc.
        Precarga miembros y mensajes.
        """
        query = select(Thread).where(
            Thread.miembros.any(id=usuario_id)
        ).options(
            selectinload(Thread.miembros),
            selectinload(Thread.mensajes).selectinload(Message.remitente)
        ).order_by(Thread.updated_at.desc())

        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def get_thread_by_id_and_member(self, thread_id: UUID, usuario_id: UUID) -> Optional[Thread]:
        """
        Busca un hilo por su ID verificando que el usuario sea miembro del mismo.
        """
        query = select(Thread).where(
            and_(
                Thread.id == thread_id,
                Thread.miembros.any(id=usuario_id)
            )
        ).options(
            selectinload(Thread.miembros),
            selectinload(Thread.mensajes).selectinload(Message.remitente)
        )

        query = self._apply_tenant_scope(query)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def save_message(self, message: Message) -> Message:
        """
        Persiste un mensaje en la base de datos.
        """
        if message.tenant_id is None:
            message.tenant_id = self.tenant_id
        self.session.add(message)
        await self.session.flush()
        return message
