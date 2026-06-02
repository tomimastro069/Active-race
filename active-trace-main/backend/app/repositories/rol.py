from typing import Optional, List
from sqlalchemy import select, or_
from app.repositories.base import BaseRepository
from app.models.rol import Rol

class RolRepository(BaseRepository[Rol]):
    """
    Repositorio para la entidad Rol.
    Soporta resolución de roles del tenant y roles globales del sistema.
    """

    async def get_by_nombre(self, nombre: str) -> Optional[Rol]:
        """
        Busca un rol por nombre. Prioriza el rol específico del tenant
        sobre el rol global por defecto del sistema.
        """
        query = select(Rol).where(
            Rol.nombre == nombre,
            Rol.deleted_at.is_(None)
        ).where(
            or_(
                Rol.tenant_id == self.tenant_id,
                Rol.tenant_id.is_(None)
            )
        ).order_by(
            Rol.tenant_id.desc()  # Ordena desc para que los no-nulos (tenant) queden primeros
        )

        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_available_roles(self) -> List[Rol]:
        """
        Retorna la lista de todos los roles visibles para el tenant:
        roles del tenant + roles globales por defecto del sistema.
        """
        query = select(Rol).where(
            Rol.deleted_at.is_(None)
        ).where(
            or_(
                Rol.tenant_id == self.tenant_id,
                Rol.tenant_id.is_(None)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
