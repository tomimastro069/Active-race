from typing import Optional
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.usuario import Usuario

class UsuarioRepository(BaseRepository[Usuario]):
    
    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """
        Busca un usuario por su email calculando su hash determinista.
        La consulta está automáticamente restringida al tenant_id del repositorio.
        """
        from app.core.security import generate_email_hash
        email_hash = generate_email_hash(email)
        return await self.get_by_email_hash(email_hash)

    async def get_by_email_hash(self, email_hash: str) -> Optional[Usuario]:
        """
        Busca un usuario directamente por su email_hash.
        La consulta está automáticamente restringida al tenant_id del repositorio.
        """
        query = select(Usuario).where(Usuario.email_hash == email_hash)
        query = self._apply_tenant_scope(query)
        
        result = await self.session.execute(query)
        return result.scalars().first()

