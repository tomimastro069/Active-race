from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, and_, or_
from sqlalchemy.orm import aliased

from app.models.asignacion import Asignacion
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.repositories.asignacion import AsignacionRepository
from app.repositories.usuario import UsuarioRepository
from app.repositories.rol import RolRepository
from app.schemas.asignacion import AsignacionMasivaCreate, EquipoClonarRequest, AsignacionVigenciaUpdate
from app.services.audit import AuditService

class EquiposService:
    """
    Servicio de dominio para gestionar equipos de forma masiva.
    """
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = AsignacionRepository(Asignacion, db, tenant_id)
        self.user_repo = UsuarioRepository(Usuario, db, tenant_id)
        self.rol_repo = RolRepository(Rol, db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    async def asignacion_masiva(self, schema: AsignacionMasivaCreate, actor_id: UUID) -> List[Asignacion]:
        """
        Asigna en lote múltiples usuarios a un rol y contexto académico.
        Toda la operación se ejecuta en una única transacción.
        """
        # 1. Validar rol existente
        rol = await self.rol_repo.get_by_id(schema.rol_id)
        if not rol:
            raise ValueError("El rol asignado no existe o pertenece a otro tenant.")

        # 2. Validar responsable si se especifica
        if schema.responsable_id:
            resp = await self.user_repo.get_by_id(schema.responsable_id)
            if not resp:
                raise ValueError("El responsable asignado no existe o pertenece a otro tenant.")

        # 3. Validar fechas
        if schema.hasta is not None and schema.desde > schema.hasta:
            raise ValueError("La fecha de inicio 'desde' no puede ser posterior a la fecha de fin 'hasta'.")

        # 4. Validar que todos los usuarios existan en el tenant activo
        query = select(Usuario).where(
            and_(
                Usuario.id.in_(schema.usuario_ids),
                Usuario.tenant_id == self.tenant_id,
                Usuario.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        db_users = result.scalars().all()
        db_user_ids = {u.id for u in db_users}
        for u_id in schema.usuario_ids:
            if u_id not in db_user_ids:
                raise ValueError(f"El usuario con ID {u_id} no existe o pertenece a otro tenant.")

        # 5. Generar inserción en bulk
        values_to_insert = []
        now = datetime.utcnow()
        for u_id in schema.usuario_ids:
            values_to_insert.append({
                "id": uuid.uuid4(),
                "tenant_id": self.tenant_id,
                "usuario_id": u_id,
                "rol_id": schema.rol_id,
                "materia_id": schema.materia_id,
                "carrera_id": schema.carrera_id,
                "cohorte_id": schema.cohorte_id,
                "comisiones": schema.comisiones,
                "responsable_id": schema.responsable_id,
                "desde": schema.desde,
                "hasta": schema.hasta,
                "created_at": now,
                "updated_at": now,
                "deleted_at": None
            })

        if values_to_insert:
            stmt = insert(Asignacion).values(values_to_insert)
            await self.db.execute(stmt)
            await self.db.flush()

            # Recuperar los registros creados
            created_ids = [v["id"] for v in values_to_insert]
            stmt_select = select(Asignacion).where(Asignacion.id.in_(created_ids))
            res_select = await self.db.execute(stmt_select)
            created_assignments = list(res_select.scalars().all())
        else:
            created_assignments = []

        # 6. Loguear en auditoría
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ASIGNACION_MASIVA",
            detalle={
                "usuario_ids": [str(uid) for uid in schema.usuario_ids],
                "rol_id": str(schema.rol_id),
                "materia_id": str(schema.materia_id) if schema.materia_id else None,
                "carrera_id": str(schema.carrera_id) if schema.carrera_id else None,
                "cohorte_id": str(schema.cohorte_id) if schema.cohorte_id else None,
                "comisiones": schema.comisiones,
                "cantidad": len(schema.usuario_ids)
            },
            filas_afectadas=len(schema.usuario_ids)
        )

        return created_assignments

    async def clonar_equipo(self, schema: EquipoClonarRequest, actor_id: UUID) -> List[Asignacion]:
        """
        Clona todas las asignaciones activas de un contexto origen a un contexto destino.
        Valida que el contexto destino no contenga asignaciones activas previas.
        """
        now = datetime.utcnow()

        # 1. Validar que el contexto destino no tenga asignaciones activas
        query_target = select(Asignacion).where(
            and_(
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.materia_id == schema.target_materia_id,
                Asignacion.cohorte_id == schema.target_cohorte_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.desde <= now,
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta >= now
                )
            )
        )
        res_target = await self.db.execute(query_target)
        if len(res_target.scalars().all()) > 0:
            raise ValueError("El contexto destino ya tiene asignaciones activas.")

        # 2. Buscar asignaciones activas en el origen
        query_source = select(Asignacion).where(
            and_(
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.materia_id == schema.source_materia_id,
                Asignacion.cohorte_id == schema.source_cohorte_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.desde <= now,
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta >= now
                )
            )
        )
        res_source = await self.db.execute(query_source)
        source_assignments = list(res_source.scalars().all())

        if not source_assignments:
            raise ValueError("El contexto origen no tiene asignaciones activas para clonar.")

        # 3. Preparar inserción de clones
        values_to_insert = []
        now_db = datetime.utcnow()
        for src in source_assignments:
            values_to_insert.append({
                "id": uuid.uuid4(),
                "tenant_id": self.tenant_id,
                "usuario_id": src.usuario_id,
                "rol_id": src.rol_id,
                "materia_id": schema.target_materia_id,
                "cohorte_id": schema.target_cohorte_id,
                "carrera_id": src.carrera_id,
                "comisiones": src.comisiones,
                "responsable_id": src.responsable_id,
                "desde": schema.nuevo_desde,
                "hasta": schema.nuevo_hasta,
                "created_at": now_db,
                "updated_at": now_db,
                "deleted_at": None
            })

        if values_to_insert:
            stmt = insert(Asignacion).values(values_to_insert)
            await self.db.execute(stmt)
            await self.db.flush()

            # Recuperar registros creados
            created_ids = [v["id"] for v in values_to_insert]
            stmt_select = select(Asignacion).where(Asignacion.id.in_(created_ids))
            res_select = await self.db.execute(stmt_select)
            cloned_assignments = list(res_select.scalars().all())
        else:
            cloned_assignments = []

        # 4. Registrar en auditoría
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ASIGNACION_CLONAR",
            detalle={
                "source_materia_id": str(schema.source_materia_id),
                "source_cohorte_id": str(schema.source_cohorte_id),
                "target_materia_id": str(schema.target_materia_id),
                "target_cohorte_id": str(schema.target_cohorte_id),
                "cantidad": len(values_to_insert)
            },
            filas_afectadas=len(values_to_insert)
        )

        return cloned_assignments

    async def modificar_vigencia_masiva(self, schema: AsignacionVigenciaUpdate, actor_id: UUID) -> List[Asignacion]:
        """
        Modifica la vigencia (desde/hasta) de todas las asignaciones asociadas a un contexto académico.
        """
        filters = [
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.deleted_at.is_(None)
        ]

        has_context = False
        if schema.materia_id is not None:
            filters.append(Asignacion.materia_id == schema.materia_id)
            has_context = True
        if schema.carrera_id is not None:
            filters.append(Asignacion.carrera_id == schema.carrera_id)
            has_context = True
        if schema.cohorte_id is not None:
            filters.append(Asignacion.cohorte_id == schema.cohorte_id)
            has_context = True

        if not has_context:
            raise ValueError("Debe especificar al menos un parámetro de contexto académico (materia, carrera o cohorte).")

        if schema.desde is None and schema.hasta is None:
            raise ValueError("Debe especificar al menos una fecha de vigencia a modificar (desde o hasta).")

        # 1. Recuperar asignaciones para validación individual
        query = select(Asignacion).where(and_(*filters))
        res = await self.db.execute(query)
        assignments = list(res.scalars().all())

        if not assignments:
            return []

        # 2. Validar fechas en cada asignación
        for asig in assignments:
            desde_check = schema.desde if schema.desde is not None else asig.desde
            hasta_check = schema.hasta if schema.hasta is not None else asig.hasta
            if hasta_check is not None and desde_check > hasta_check:
                raise ValueError("La fecha de inicio 'desde' no puede ser posterior a la fecha de fin 'hasta'.")

        # 3. Aplicar actualización
        update_values = {}
        if schema.desde is not None:
            update_values["desde"] = schema.desde
        if schema.hasta is not None:
            update_values["hasta"] = schema.hasta

        stmt = update(Asignacion).where(and_(*filters)).values(**update_values)
        await self.db.execute(stmt)
        await self.db.flush()

        # 4. Recuperar asignaciones actualizadas
        res_updated = await self.db.execute(query)
        updated_assignments = list(res_updated.scalars().all())

        # 5. Registrar en auditoría
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ASIGNACION_VIGENCIA_MASIVA",
            detalle={
                "materia_id": str(schema.materia_id) if schema.materia_id else None,
                "carrera_id": str(schema.carrera_id) if schema.carrera_id else None,
                "cohorte_id": str(schema.cohorte_id) if schema.cohorte_id else None,
                "desde": schema.desde.isoformat() if schema.desde else None,
                "hasta": schema.hasta.isoformat() if schema.hasta else None,
                "cantidad": len(updated_assignments)
            },
            filas_afectadas=len(updated_assignments)
        )

        return updated_assignments

    async def obtener_mis_equipos(self, usuario_id: UUID) -> List[Asignacion]:
        """
        Retorna las asignaciones correspondientes al usuario especificado.
        """
        query = select(Asignacion).where(
            and_(
                Asignacion.usuario_id == usuario_id,
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.deleted_at.is_(None)
            )
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def exportar_equipo(
        self,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None
    ) -> str:
        """
        Exporta las asignaciones activas de un contexto académico a formato CSV.
        """
        if materia_id is None and carrera_id is None and cohorte_id is None:
            raise ValueError("Debe especificar al menos un parámetro de contexto académico (materia, carrera o cohorte).")

        filters = [
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.deleted_at.is_(None)
        ]
        if materia_id is not None:
            filters.append(Asignacion.materia_id == materia_id)
        if carrera_id is not None:
            filters.append(Asignacion.carrera_id == carrera_id)
        if cohorte_id is not None:
            filters.append(Asignacion.cohorte_id == cohorte_id)

        now = datetime.utcnow()
        filters.append(Asignacion.desde <= now)
        filters.append(
            or_(
                Asignacion.hasta.is_(None),
                Asignacion.hasta >= now
            )
        )

        Responsable = aliased(Usuario)

        query = select(
            Usuario.nombre,
            Usuario.apellidos,
            Usuario.email,
            Rol.nombre.label("rol_nombre"),
            Asignacion.desde,
            Asignacion.hasta,
            Asignacion.comisiones,
            Responsable.nombre.label("responsable_nombre"),
            Responsable.apellidos.label("responsable_apellidos")
        ).join(Usuario, Usuario.id == Asignacion.usuario_id).\
          join(Rol, Rol.id == Asignacion.rol_id).\
          outerjoin(Responsable, Responsable.id == Asignacion.responsable_id).\
          where(and_(*filters))

        res = await self.db.execute(query)
        rows = res.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Nombre", "Apellidos", "Email", "Rol", "Desde", "Hasta", "Comisiones", "Responsable"])

        for row in rows:
            comisiones_str = ", ".join(row.comisiones) if row.comisiones else ""
            resp_name = f"{row.responsable_nombre} {row.responsable_apellidos}" if row.responsable_nombre else ""
            writer.writerow([
                row.nombre or "",
                row.apellidos or "",
                row.email or "",
                row.rol_nombre or "",
                row.desde.isoformat() if row.desde else "",
                row.hasta.isoformat() if row.hasta else "",
                comisiones_str,
                resp_name.strip()
            ])

        return output.getvalue()
