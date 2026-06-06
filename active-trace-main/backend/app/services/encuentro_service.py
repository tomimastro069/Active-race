from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, date, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, DiaSemanaEnum, EstadoEncuentroEnum
from app.repositories.encuentro_repository import SlotEncuentroRepository, InstanciaEncuentroRepository
from app.schemas.encuentro import SlotEncuentroCreate, InstanciaEncuentroUpdate
from app.services.audit import AuditService

WEEKDAY_MAP = {
    DiaSemanaEnum.LUNES: 0,
    DiaSemanaEnum.MARTES: 1,
    DiaSemanaEnum.MIERCOLES: 2,
    DiaSemanaEnum.JUEVES: 3,
    DiaSemanaEnum.VIERNES: 4,
    DiaSemanaEnum.SABADO: 5,
    DiaSemanaEnum.DOMINGO: 6,
}

class EncuentroService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.slot_repo = SlotEncuentroRepository(db, tenant_id)
        self.instancia_repo = InstanciaEncuentroRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    async def crear_encuentro_recurrente(
        self, schema: SlotEncuentroCreate, actor_id: UUID
    ) -> Tuple[SlotEncuentro, List[InstanciaEncuentro]]:
        # 1. Crear SlotEncuentro
        slot = SlotEncuentro(
            materia_id=schema.materia_id,
            titulo=schema.titulo,
            hora=schema.hora,
            dia_semana=schema.dia_semana,
            fecha_inicio=schema.fecha_inicio,
            cant_semanas=schema.cant_semanas,
            meet_url=schema.meet_url
        )
        slot = await self.slot_repo.create(slot)
        await self.db.flush()

        # 2. Generar Instancias
        target_weekday = WEEKDAY_MAP[schema.dia_semana]
        start_weekday = schema.fecha_inicio.weekday()
        days_ahead = (target_weekday - start_weekday) % 7
        first_date = schema.fecha_inicio + timedelta(days=days_ahead)

        instancias = []
        for i in range(schema.cant_semanas):
            inst_date = first_date + timedelta(days=7 * i)
            inst_datetime = datetime.combine(inst_date, schema.hora)
            instancia = InstanciaEncuentro(
                slot_id=slot.id,
                materia_id=schema.materia_id,
                titulo=f"{schema.titulo} - Semana {i + 1}",
                fecha_hora=inst_datetime,
                estado=EstadoEncuentroEnum.PROGRAMADO,
                meet_url=schema.meet_url
            )
            instancia = await self.instancia_repo.create(instancia)
            instancias.append(instancia)
        
        await self.db.flush()

        # 3. Loguear en auditoría
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ENCUENTRO_RECURRENTE_CREAR",
            materia_id=schema.materia_id,
            detalle={
                "slot_id": str(slot.id),
                "titulo": slot.titulo,
                "cant_semanas": slot.cant_semanas,
                "instancias_generadas": len(instancias)
            }
        )

        return slot, instancias

    async def crear_encuentro_unico(
        self, titulo: str, materia_id: UUID, fecha_hora: datetime, meet_url: Optional[str], actor_id: UUID
    ) -> InstanciaEncuentro:
        instancia = InstanciaEncuentro(
            slot_id=None,
            materia_id=materia_id,
            titulo=titulo,
            fecha_hora=fecha_hora,
            estado=EstadoEncuentroEnum.PROGRAMADO,
            meet_url=meet_url
        )
        instancia = await self.instancia_repo.create(instancia)
        await self.db.flush()

        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="ENCUENTRO_UNICO_CREAR",
            materia_id=materia_id,
            detalle={
                "instancia_id": str(instancia.id),
                "titulo": instancia.titulo,
                "fecha_hora": instancia.fecha_hora.isoformat()
            }
        )
        return instancia

    async def update_instancia(
        self, instancia_id: UUID, schema: InstanciaEncuentroUpdate, actor_id: UUID
    ) -> InstanciaEncuentro:
        instancia = await self.instancia_repo.get_by_id(instancia_id)
        if not instancia:
            raise ValueError("La instancia no existe o pertenece a otro tenant.")

        detalle_cambio = {}
        if schema.estado is not None and schema.estado != instancia.estado:
            detalle_cambio["estado_antiguo"] = instancia.estado
            detalle_cambio["estado_nuevo"] = schema.estado
            instancia.estado = schema.estado

        if schema.meet_url is not None and schema.meet_url != instancia.meet_url:
            detalle_cambio["meet_url_antiguo"] = instancia.meet_url
            detalle_cambio["meet_url_nuevo"] = schema.meet_url
            instancia.meet_url = schema.meet_url

        if schema.video_url is not None and schema.video_url != instancia.video_url:
            detalle_cambio["video_url_antiguo"] = instancia.video_url
            detalle_cambio["video_url_nuevo"] = schema.video_url
            instancia.video_url = schema.video_url

        if schema.comentario is not None and schema.comentario != instancia.comentario:
            detalle_cambio["comentario_antiguo"] = instancia.comentario
            detalle_cambio["comentario_nuevo"] = schema.comentario
            instancia.comentario = schema.comentario

        if not detalle_cambio:
            return instancia

        instancia = await self.instancia_repo.update(instancia)
        await self.db.flush()

        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="INSTANCIA_ENCUENTRO_MODIFICAR",
            materia_id=instancia.materia_id,
            detalle={"instancia_id": str(instancia.id), **detalle_cambio}
        )
        return instancia
