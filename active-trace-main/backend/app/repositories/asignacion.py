from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, or_
from app.repositories.base import BaseRepository
from app.models.asignacion import Asignacion
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.permiso import Permiso

class AsignacionRepository(BaseRepository[Asignacion]):
    """
    Repositorio para la entidad Asignacion.
    Resuelve permisos efectivos en base a vigencias temporales.
    """

    async def get_effective_permissions(self, usuario_id: UUID) -> List[str]:
        """
        Retorna la unión de nombres de permisos activos y vigentes para el usuario.
        """
        now = datetime.utcnow()
        query = select(Permiso.nombre).distinct().\
            join(RolPermiso, RolPermiso.permiso_id == Permiso.id).\
            join(Rol, Rol.id == RolPermiso.rol_id).\
            join(Asignacion, Asignacion.rol_id == Rol.id).\
            where(
                Asignacion.usuario_id == usuario_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.desde <= now,
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta >= now
                )
            ).where(
                Permiso.deleted_at.is_(None),
                Rol.deleted_at.is_(None),
                RolPermiso.deleted_at.is_(None)
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_roles(self, usuario_id: UUID) -> List[str]:
        """
        Retorna la lista de nombres de roles activos y vigentes para el usuario.
        """
        now = datetime.utcnow()
        query = select(Rol.nombre).distinct().\
            join(Asignacion, Asignacion.rol_id == Rol.id).\
            where(
                Asignacion.usuario_id == usuario_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.desde <= now,
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta >= now
                ),
                Rol.deleted_at.is_(None)
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_assignments(
        self,
        usuario_id: Optional[UUID] = None,
        rol_id: Optional[UUID] = None,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Asignacion]:
        """
        Lista asignaciones con filtros opcionales.
        La consulta está automáticamente restringida al tenant_id del repositorio.
        """
        query = select(Asignacion)
        if usuario_id:
            query = query.where(Asignacion.usuario_id == usuario_id)
        if rol_id:
            query = query.where(Asignacion.rol_id == rol_id)
        if materia_id:
            query = query.where(Asignacion.materia_id == materia_id)
        if carrera_id:
            query = query.where(Asignacion.carrera_id == carrera_id)
        if cohorte_id:
            query = query.where(Asignacion.cohorte_id == cohorte_id)
        
        query = self._apply_tenant_scope(query)
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

