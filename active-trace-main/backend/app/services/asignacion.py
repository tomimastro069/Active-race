from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.asignacion import Asignacion
from app.repositories.asignacion import AsignacionRepository
from app.repositories.usuario import UsuarioRepository
from app.repositories.rol import RolRepository
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.schemas.asignacion import AsignacionCreate, AsignacionUpdate
from app.services.audit import AuditService

class AsignacionService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = AsignacionRepository(Asignacion, db, tenant_id)
        self.user_repo = UsuarioRepository(Usuario, db, tenant_id)
        self.rol_repo = RolRepository(Rol, db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    async def create_assignment(self, schema: AsignacionCreate, actor_id: UUID) -> Asignacion:
        # 1. Validar que el usuario existe
        usuario = await self.user_repo.get_by_id(schema.usuario_id)
        if not usuario:
            raise ValueError("El usuario asignado no existe o pertenece a otro tenant.")

        # 2. Validar que el rol existe
        rol = await self.rol_repo.get_by_id(schema.rol_id)
        if not rol:
            raise ValueError("El rol asignado no existe o pertenece a otro tenant.")

        # 3. Validar fechas
        if schema.hasta is not None and schema.desde > schema.hasta:
            raise ValueError("La fecha de inicio 'desde' no puede ser posterior a la fecha de fin 'hasta'.")

        # 4. Validar responsable si se especifica
        if schema.responsable_id:
            resp = await self.user_repo.get_by_id(schema.responsable_id)
            if not resp:
                raise ValueError("El responsable asignado no existe o pertenece a otro tenant.")

        # 5. Crear la asignación
        asig = Asignacion(
            usuario_id=schema.usuario_id,
            rol_id=schema.rol_id,
            materia_id=schema.materia_id,
            carrera_id=schema.carrera_id,
            cohorte_id=schema.cohorte_id,
            comisiones=schema.comisiones,
            responsable_id=schema.responsable_id,
            desde=schema.desde,
            hasta=schema.hasta
        )

        asig = await self.repo.create(asig)
        await self.db.flush()

        # Loguear en auditoría
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ASIGNACION_CREAR",
            detalle={
                "id": str(asig.id),
                "usuario_id": str(asig.usuario_id),
                "rol_id": str(asig.rol_id)
            }
        )
        return asig

    async def update_assignment(self, asig_id: UUID, schema: AsignacionUpdate, actor_id: UUID) -> Asignacion:
        asig = await self.repo.get_by_id(asig_id)
        if not asig:
            raise ValueError("La asignación no existe o pertenece a otro tenant.")

        detalle_cambio = {}

        # Validaciones de relaciones si cambian
        if schema.rol_id is not None and schema.rol_id != asig.rol_id:
            rol = await self.rol_repo.get_by_id(schema.rol_id)
            if not rol:
                raise ValueError("El rol asignado no existe o pertenece a otro tenant.")
            detalle_cambio["rol_id_antiguo"] = str(asig.rol_id)
            detalle_cambio["rol_id_nuevo"] = str(schema.rol_id)
            asig.rol_id = schema.rol_id

        if schema.responsable_id is not None and schema.responsable_id != asig.responsable_id:
            if schema.responsable_id:
                resp = await self.user_repo.get_by_id(schema.responsable_id)
                if not resp:
                    raise ValueError("El responsable asignado no existe o pertenece a otro tenant.")
            detalle_cambio["responsable_id_antiguo"] = str(asig.responsable_id) if asig.responsable_id else None
            detalle_cambio["responsable_id_nuevo"] = str(schema.responsable_id) if schema.responsable_id else None
            asig.responsable_id = schema.responsable_id

        # Validar fechas
        desde_check = schema.desde if schema.desde is not None else asig.desde
        hasta_check = schema.hasta if schema.hasta is not None else asig.hasta

        if hasta_check is not None and desde_check > hasta_check:
            raise ValueError("La fecha de inicio 'desde' no puede ser posterior a la fecha de fin 'hasta'.")

        if schema.desde is not None and schema.desde != asig.desde:
            detalle_cambio["desde_antiguo"] = asig.desde.isoformat()
            detalle_cambio["desde_nuevo"] = schema.desde.isoformat()
            asig.desde = schema.desde

        if schema.hasta is not None and schema.hasta != asig.hasta:
            detalle_cambio["hasta_antiguo"] = asig.hasta.isoformat() if asig.hasta else None
            detalle_cambio["hasta_nuevo"] = schema.hasta.isoformat() if schema.hasta else None
            asig.hasta = schema.hasta

        # Contexto
        for field in ["materia_id", "carrera_id", "cohorte_id", "comisiones"]:
            val = getattr(schema, field)
            if val is not None:
                old_val = getattr(asig, field)
                if val != old_val:
                    detalle_cambio[f"{field}_antiguo"] = str(old_val) if old_val else None
                    detalle_cambio[f"{field}_nuevo"] = str(val) if val else None
                    setattr(asig, field, val)

        if not detalle_cambio:
            return asig

        asig = await self.repo.update(asig)
        await self.db.flush()

        # Loguear en auditoría
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ASIGNACION_MODIFICAR",
            detalle={"id": str(asig.id), **detalle_cambio}
        )
        return asig

    async def delete_assignment(self, asig_id: UUID, actor_id: UUID) -> None:
        asig = await self.repo.get_by_id(asig_id)
        if not asig:
            raise ValueError("La asignación no existe o pertenece a otro tenant.")

        await self.repo.delete_logical(asig_id)
        await self.db.flush()

        # Loguear en auditoría
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ASIGNACION_ELIMINAR",
            detalle={"id": str(asig_id)}
        )

    async def get_assignment(self, asig_id: UUID) -> Optional[Asignacion]:
        return await self.repo.get_by_id(asig_id)

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
        return await self.repo.list_assignments(
            usuario_id=usuario_id,
            rol_id=rol_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            skip=skip,
            limit=limit
        )
