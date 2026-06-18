from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.models.evaluacion import (
    Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, ConvocadoEvaluacion,
    EstadoReservaEnum, EvaluacionTipoEnum,
)
from app.models.usuario import Usuario
from app.schemas.evaluacion import ReservaCreate

class CRUDEvaluacion:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def reservar_evaluacion(self, reserva_in: ReservaCreate) -> ReservaEvaluacion:
        # 1. Lock the Evaluacion row for update
        stmt = select(Evaluacion).where(
            Evaluacion.id == reserva_in.evaluacion_id,
            Evaluacion.tenant_id == self.tenant_id
        ).with_for_update()
        result = await self.db.execute(stmt)
        evaluacion = result.scalar_one_or_none()

        if not evaluacion:
            raise ValueError("Evaluación no encontrada")

        # 2. Check current active reservations
        stmt_count = select(func.count(ReservaEvaluacion.id)).where(
            ReservaEvaluacion.evaluacion_id == evaluacion.id,
            ReservaEvaluacion.estado == EstadoReservaEnum.ACTIVA
        )
        count_result = await self.db.execute(stmt_count)
        current_reservations = count_result.scalar_one()

        # 3. Verify cupos
        if current_reservations >= evaluacion.cupos_totales:
            raise ValueError("No hay cupos disponibles")

        # 4. Check if student already has a reservation
        stmt_dup = select(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion.id,
            ReservaEvaluacion.alumno_id == reserva_in.alumno_id,
            ReservaEvaluacion.estado == EstadoReservaEnum.ACTIVA
        )
        dup_result = await self.db.execute(stmt_dup)
        if dup_result.scalar_one_or_none():
            raise ValueError("El alumno ya tiene una reserva activa")

        # 5. Create reservation
        reserva = ReservaEvaluacion(
            tenant_id=self.tenant_id,
            evaluacion_id=reserva_in.evaluacion_id,
            alumno_id=reserva_in.alumno_id,
            fecha_hora=reserva_in.fecha_hora,
            estado=EstadoReservaEnum.ACTIVA
        )
        self.db.add(reserva)
        
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("El alumno ya tiene una reserva activa")

        return reserva

    async def listar_evaluaciones(
        self,
        tipo: Optional[EvaluacionTipoEnum] = None,
        materia_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        orden_por_fecha: bool = False,
    ) -> List[dict]:
        """Lista evaluaciones del tenant con contadores de convocados/reservas/cupos (HU-31).

        Con ``orden_por_fecha`` ordena por la fecha académica (vista calendario, HU-24).
        """
        stmt = select(Evaluacion).where(
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.deleted_at.is_(None),
        )
        if tipo is not None:
            stmt = stmt.where(Evaluacion.tipo == tipo)
        if materia_id is not None:
            stmt = stmt.where(Evaluacion.materia_id == materia_id)
        if cohorte_id is not None:
            stmt = stmt.where(Evaluacion.cohorte_id == cohorte_id)
        orden = Evaluacion.fecha.asc() if orden_por_fecha else Evaluacion.created_at.desc()
        result = await self.db.execute(stmt.order_by(orden))
        evaluaciones = result.scalars().all()

        resumenes: List[dict] = []
        for ev in evaluaciones:
            convocados = await self.db.scalar(
                select(func.count(ConvocadoEvaluacion.id)).where(
                    ConvocadoEvaluacion.evaluacion_id == ev.id,
                    ConvocadoEvaluacion.deleted_at.is_(None),
                )
            )
            reservas_activas = await self.db.scalar(
                select(func.count(ReservaEvaluacion.id)).where(
                    ReservaEvaluacion.evaluacion_id == ev.id,
                    ReservaEvaluacion.estado == EstadoReservaEnum.ACTIVA,
                    ReservaEvaluacion.deleted_at.is_(None),
                )
            )
            resumenes.append({
                "id": ev.id,
                "materia_id": ev.materia_id,
                "cohorte_id": ev.cohorte_id,
                "tipo": ev.tipo,
                "instancia": ev.instancia,
                "titulo": ev.titulo,
                "fecha": ev.fecha,
                "dias_disponibles": ev.dias_disponibles,
                "cupos_totales": ev.cupos_totales,
                "convocados": convocados or 0,
                "reservas_activas": reservas_activas or 0,
                "cupos_disponibles": max(ev.cupos_totales - (reservas_activas or 0), 0),
            })
        return resumenes

    async def importar_convocados(self, evaluacion_id: UUID, alumno_ids: List[UUID]) -> dict:
        """Carga el padrón de alumnos elegibles de una instancia de coloquio (HU-30)."""
        evaluacion = await self.db.scalar(
            select(Evaluacion).where(
                Evaluacion.id == evaluacion_id,
                Evaluacion.tenant_id == self.tenant_id,
                Evaluacion.deleted_at.is_(None),
            )
        )
        if not evaluacion:
            raise ValueError("Evaluación no encontrada")

        existentes = set(
            (await self.db.execute(
                select(ConvocadoEvaluacion.alumno_id).where(
                    ConvocadoEvaluacion.evaluacion_id == evaluacion_id,
                    ConvocadoEvaluacion.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        nuevos = 0
        for alumno_id in dict.fromkeys(alumno_ids):  # dedup preservando orden
            if alumno_id in existentes:
                continue
            self.db.add(ConvocadoEvaluacion(
                tenant_id=self.tenant_id,
                evaluacion_id=evaluacion_id,
                alumno_id=alumno_id,
            ))
            nuevos += 1
        await self.db.flush()
        return {
            "evaluacion_id": evaluacion_id,
            "convocados_nuevos": nuevos,
            "convocados_totales": len(existentes) + nuevos,
        }

    async def obtener_agenda(
        self,
        materia_id: Optional[UUID] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> List[dict]:
        """Agenda consolidada de reservas activas con filtros (HU-32)."""
        stmt = (
            select(ReservaEvaluacion, Evaluacion, Usuario)
            .join(Evaluacion, Evaluacion.id == ReservaEvaluacion.evaluacion_id)
            .join(Usuario, Usuario.id == ReservaEvaluacion.alumno_id)
            .where(
                ReservaEvaluacion.tenant_id == self.tenant_id,
                ReservaEvaluacion.estado == EstadoReservaEnum.ACTIVA,
                ReservaEvaluacion.deleted_at.is_(None),
            )
        )
        if materia_id is not None:
            stmt = stmt.where(Evaluacion.materia_id == materia_id)
        if desde is not None:
            stmt = stmt.where(ReservaEvaluacion.fecha_hora >= desde)
        if hasta is not None:
            stmt = stmt.where(ReservaEvaluacion.fecha_hora <= hasta)
        if search:
            patron = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(func.concat(Usuario.nombre, ' ', Usuario.apellidos)).like(patron)
            )
        result = await self.db.execute(stmt.order_by(ReservaEvaluacion.fecha_hora))
        agenda: List[dict] = []
        for reserva, evaluacion, alumno in result.all():
            nombre = " ".join(p for p in [alumno.nombre, alumno.apellidos] if p) or None
            agenda.append({
                "reserva_id": reserva.id,
                "evaluacion_id": evaluacion.id,
                "materia_id": evaluacion.materia_id,
                "instancia": evaluacion.instancia,
                "alumno_id": alumno.id,
                "alumno_nombre": nombre,
                "fecha_hora": reserva.fecha_hora,
                "estado": reserva.estado,
            })
        return agenda

    async def cargar_resultado(self, evaluacion_id: UUID, alumno_id: UUID, nota_final: str) -> ResultadoEvaluacion:
        """Registra/actualiza la nota final de un alumno en una instancia (HU-33)."""
        evaluacion = await self.db.scalar(
            select(Evaluacion).where(
                Evaluacion.id == evaluacion_id,
                Evaluacion.tenant_id == self.tenant_id,
                Evaluacion.deleted_at.is_(None),
            )
        )
        if not evaluacion:
            raise ValueError("Evaluación no encontrada")

        resultado = await self.db.scalar(
            select(ResultadoEvaluacion).where(
                ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                ResultadoEvaluacion.alumno_id == alumno_id,
                ResultadoEvaluacion.deleted_at.is_(None),
            )
        )
        if resultado:
            resultado.nota_final = nota_final
        else:
            resultado = ResultadoEvaluacion(
                tenant_id=self.tenant_id,
                evaluacion_id=evaluacion_id,
                alumno_id=alumno_id,
                nota_final=nota_final,
            )
            self.db.add(resultado)
        await self.db.flush()
        return resultado

    async def obtener_registro_academico(self, evaluacion_id: Optional[UUID] = None) -> List[dict]:
        """Registro académico consolidado de notas finales de coloquios (HU-33)."""
        stmt = (
            select(ResultadoEvaluacion, Usuario)
            .join(Usuario, Usuario.id == ResultadoEvaluacion.alumno_id)
            .where(
                ResultadoEvaluacion.tenant_id == self.tenant_id,
                ResultadoEvaluacion.deleted_at.is_(None),
            )
        )
        if evaluacion_id is not None:
            stmt = stmt.where(ResultadoEvaluacion.evaluacion_id == evaluacion_id)
        result = await self.db.execute(stmt.order_by(ResultadoEvaluacion.created_at.desc()))
        registro: List[dict] = []
        for resultado, alumno in result.all():
            nombre = " ".join(p for p in [alumno.nombre, alumno.apellidos] if p) or None
            registro.append({
                "id": resultado.id,
                "evaluacion_id": resultado.evaluacion_id,
                "alumno_id": resultado.alumno_id,
                "alumno_nombre": nombre,
                "nota_final": resultado.nota_final,
            })
        return registro
