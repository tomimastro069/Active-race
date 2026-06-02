from typing import Optional, List
from sqlalchemy import select, or_
from app.repositories.base import BaseRepository
from app.models.permiso import Permiso

class PermisoRepository(BaseRepository[Permiso]):
    """
    Repositorio para la entidad Permiso.
    Soporta resolución de permisos locales y globales.
    """

    async def get_by_nombre(self, nombre: str) -> Optional[Permiso]:
        """
        Busca un permiso por nombre en el tenant actual o globales.
        """
        query = select(Permiso).where(
            Permiso.nombre == nombre,
            Permiso.deleted_at.is_(None)
        ).where(
            or_(
                Permiso.tenant_id == self.tenant_id,
                Permiso.tenant_id.is_(None)
            )
        ).order_by(
            Permiso.tenant_id.desc()
        )

        result = await self.session.execute(query)
        return result.scalars().first()
