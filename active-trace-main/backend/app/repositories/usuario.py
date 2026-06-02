from typing import Optional
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.usuario import Usuario

class UsuarioRepository(BaseRepository[Usuario]):
    
    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """
        Busca un usuario por su email.
        La consulta está automáticamente restringida al tenant_id del repositorio.
        """
        query = select(Usuario).where(Usuario.email == email)
        query = self._apply_tenant_scope(query)
        
        result = await self.session.execute(query)
        return result.scalars().first()
