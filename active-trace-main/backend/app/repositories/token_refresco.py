from typing import Optional
from sqlalchemy import select, delete
from app.repositories.base import BaseRepository
from app.models.token_refresco import TokenRefresco

class TokenRefrescoRepository(BaseRepository[TokenRefresco]):
    
    async def get_by_token(self, token: str) -> Optional[TokenRefresco]:
        """
        Busca un token de refresco.
        La consulta está restringida al tenant_id del repositorio.
        """
        query = select(TokenRefresco).where(TokenRefresco.token == token)
        query = self._apply_tenant_scope(query)
        
        result = await self.session.execute(query)
        return result.scalars().first()
        
    async def revoke_family(self, familia_id: str) -> None:
        """
        Elimina (revoca) físicamente todos los tokens de una misma familia.
        Esto se usa cuando se detecta el reuso de un token (ataque) o en el logout.
        """
        query = delete(TokenRefresco).where(TokenRefresco.familia_id == familia_id)
        if self.tenant_id is not None:
            query = query.where(TokenRefresco.tenant_id == self.tenant_id)
            
        await self.session.execute(query)
        await self.session.flush()
