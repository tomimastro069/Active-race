from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import Tarea, ComentarioTarea, EstadoTareaEnum
from app.repositories.tarea_repository import TareaRepository, ComentarioTareaRepository
from app.schemas.tarea import TareaCreate, TareaUpdate, ComentarioTareaCreate
from app.schemas.auth import CurrentUser

class TareaService:
    def __init__(self, db: AsyncSession, current_user: CurrentUser):
        self.db = db
        self.current_user = current_user
        self.tarea_repo = TareaRepository(db, current_user.tenant_id)
        self.comentario_repo = ComentarioTareaRepository(db, current_user.tenant_id)
        
        # Check explicit permissions (these would typically be verified by the route dependencies, 
        # but the service needs to know if the user has GLOBAL access vs ONLY _propio)
        self.has_global_manage = False
        
    async def _resolve_permissions(self):
        from app.models.asignacion import Asignacion
        from app.repositories.asignacion import AsignacionRepository
        asignacion_repo = AsignacionRepository(Asignacion, self.db, self.current_user.tenant_id)
        perms = await asignacion_repo.get_effective_permissions(self.current_user.id)
        self.has_global_manage = "tareas:gestionar" in perms

    async def get_tareas(self, skip: int = 0, limit: int = 100) -> List[Tarea]:
        await self._resolve_permissions()
        if self.has_global_manage:
            return await self.tarea_repo.list_all(skip=skip, limit=limit)
        else:
            return await self.tarea_repo.get_by_asignado(self.current_user.id, skip=skip, limit=limit)

    async def get_tarea(self, tarea_id: UUID) -> Tarea:
        await self._resolve_permissions()
        tarea = await self.tarea_repo.get_by_id(tarea_id)
        if not tarea:
            raise ValueError("Tarea no encontrada")
        
        if not self.has_global_manage and self.current_user.id not in [tarea.asignado_a, tarea.asignado_por]:
            raise PermissionError("No tienes permiso para ver esta tarea")
            
        return tarea

    async def create_tarea(self, tarea_in: TareaCreate) -> Tarea:
        await self._resolve_permissions()
        if not self.has_global_manage:
            raise PermissionError("Solo usuarios con tareas:gestionar pueden crear tareas")
            
        tarea = Tarea(
            tenant_id=self.current_user.tenant_id,
            materia_id=tarea_in.materia_id,
            asignado_a=tarea_in.asignado_a,
            asignado_por=self.current_user.id,
            estado=EstadoTareaEnum.PENDIENTE,
            descripcion=tarea_in.descripcion,
            contexto_id=tarea_in.contexto_id
        )
        return await self.tarea_repo.create(tarea)

    async def update_tarea(self, tarea_id: UUID, tarea_in: TareaUpdate) -> Tarea:
        await self._resolve_permissions()
        tarea = await self.tarea_repo.get_by_id(tarea_id)
        if not tarea:
            raise ValueError("Tarea no encontrada")
            
        if not self.has_global_manage and self.current_user.id not in [tarea.asignado_a, tarea.asignado_por]:
            raise PermissionError("No tienes permiso para modificar esta tarea")

        if tarea_in.descripcion is not None:
            # Only creator or global manager can change description
            if not self.has_global_manage and self.current_user.id != tarea.asignado_por:
                raise PermissionError("Solo el creador o un coordinador puede modificar la descripción")
            tarea.descripcion = tarea_in.descripcion
            
        if tarea_in.estado is not None:
            tarea.estado = tarea_in.estado
            
        return await self.tarea_repo.update(tarea)

    async def get_comentarios(self, tarea_id: UUID) -> List[ComentarioTarea]:
        # get_tarea validates permissions to access the task
        await self.get_tarea(tarea_id)
        return await self.comentario_repo.get_by_tarea(tarea_id)

    async def add_comentario(self, tarea_id: UUID, comentario_in: ComentarioTareaCreate) -> ComentarioTarea:
        # get_tarea validates permissions to access the task
        await self.get_tarea(tarea_id)
        comentario = ComentarioTarea(
            tenant_id=self.current_user.tenant_id,
            tarea_id=tarea_id,
            autor_id=self.current_user.id,
            texto=comentario_in.texto
        )
        return await self.comentario_repo.create(comentario)
