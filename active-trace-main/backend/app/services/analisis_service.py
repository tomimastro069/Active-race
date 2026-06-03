from typing import List, Tuple, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.calificacion import CalificacionRepository
from app.repositories.umbral import UmbralMateriaRepository
from app.repositories.padron_repository import PadronRepository
from app.repositories.asignacion import AsignacionRepository
from app.models.asignacion import Asignacion
from app.schemas.auth import CurrentUser

class AnalisisService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.calif_repo = CalificacionRepository(db, tenant_id)
        self.umbral_repo = UmbralMateriaRepository(db, tenant_id)
        self.padron_repo = PadronRepository(db, tenant_id)
        self.asignacion_repo = AsignacionRepository(Asignacion, db, tenant_id)

    async def _check_access_and_get_docente_filter(
        self,
        current_user: CurrentUser,
        materia_id: UUID,
        docente_id: Optional[UUID] = None
    ) -> Optional[UUID]:
        """
        Enforces permissions and checks user access to a subject.
        """
        effective_permissions = await self.asignacion_repo.get_effective_permissions(current_user.id)
        
        # If user has the global permission, they can access all data
        if "atrasados:ver" in effective_permissions:
            return docente_id
            
        # If user only has own permissions, they are restricted to their own ID
        if "atrasados:ver_propio" in effective_permissions:
            if docente_id and docente_id != current_user.id:
                raise ValueError("No tiene permiso para ver información de otros docentes")
            
            # Check for active assignment for the given subject
            assignments = await self.asignacion_repo.list_assignments(
                usuario_id=current_user.id,
                materia_id=materia_id
            )
            active_assignment = None
            for a in assignments:
                if a.estado_vigencia == "Vigente":
                    active_assignment = a
                    break
                    
            if not active_assignment:
                raise ValueError("El docente no tiene una asignación vigente para la materia especificada.")
                
            return current_user.id
            
        # Fallback: No permission
        raise ValueError("Permisos insuficientes para realizar esta operación.")

    async def _get_threshold_config(
        self,
        docente_id: Optional[UUID],
        materia_id: UUID
    ) -> Tuple[int, List[str]]:
        default_pct = 60
        default_valores = ["Satisfactorio", "Supera lo esperado"]

        if not docente_id:
            return default_pct, default_valores

        assignments = await self.asignacion_repo.list_assignments(
            usuario_id=docente_id,
            materia_id=materia_id
        )
        active_assignment = None
        for a in assignments:
            if a.estado_vigencia == "Vigente":
                active_assignment = a
                break

        if not active_assignment:
            return default_pct, default_valores

        umbral = await self.umbral_repo.get_by_asignacion_y_materia(
            asignacion_id=active_assignment.id,
            materia_id=materia_id
        )
        if not umbral:
            return default_pct, default_valores

        valores = umbral.valores_aprobatorios if umbral.valores_aprobatorios is not None else default_valores
        return umbral.umbral_pct, valores

    async def obtener_alumnos_atrasados(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        current_user: CurrentUser,
        docente_id: Optional[UUID] = None,
        comision: Optional[str] = None
    ) -> List[dict]:
        docente_filter = await self._check_access_and_get_docente_filter(current_user, materia_id, docente_id)
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            raise ValueError("No existe un padrón activo para la materia y cohorte especificadas.")
            
        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        if comision:
            entradas = [e for e in entradas if e.comision == comision]
            
        distinct_activities = await self.calif_repo.get_distinct_activities(materia_id, docente_filter)
        calificaciones = await self.calif_repo.get_calificaciones_by_materia(materia_id, docente_filter)
        
        calif_map = {}
        for c in calificaciones:
            calif_map[(c.entrada_padron_id, c.actividad)] = c
            
        umbral_pct, valores_aprobatorios = await self._get_threshold_config(docente_filter, materia_id)
        valores_aprobatorios_lower = {v.strip().lower() for v in valores_aprobatorios}
        
        atrasados = []
        for e in entradas:
            for act in distinct_activities:
                c = calif_map.get((e.id, act))
                is_delayed = False
                motivo = ""
                
                if not c or not c.finalizado:
                    is_delayed = True
                    motivo = "Faltante"
                else:
                    if c.es_numerica:
                        if c.nota_numerica is None:
                            is_delayed = True
                            motivo = "Faltante"
                        elif c.nota_numerica < umbral_pct:
                            is_delayed = True
                            motivo = "Nota menor al umbral"
                    else:
                        if not c.nota_textual:
                            is_delayed = True
                            motivo = "Faltante"
                        elif c.nota_textual.strip().lower() not in valores_aprobatorios_lower:
                            is_delayed = True
                            motivo = "Nota menor al umbral"
                
                if is_delayed:
                    atrasados.append({
                        "padron_id": e.id,
                        "nombre": e.nombre,
                        "apellido": e.apellidos,
                        "actividad": act,
                        "motivo": motivo
                    })
        return atrasados

    async def obtener_ranking_aprobados(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        current_user: CurrentUser,
        docente_id: Optional[UUID] = None,
        comision: Optional[str] = None
    ) -> List[dict]:
        docente_filter = await self._check_access_and_get_docente_filter(current_user, materia_id, docente_id)
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            raise ValueError("No existe un padrón activo para la materia y cohorte especificadas.")
            
        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        if comision:
            entradas = [e for e in entradas if e.comision == comision]
            
        calificaciones = await self.calif_repo.get_calificaciones_by_materia(materia_id, docente_filter)
        
        approved_counts = {}
        for c in calificaciones:
            if c.aprobado:
                approved_counts[c.entrada_padron_id] = approved_counts.get(c.entrada_padron_id, 0) + 1
                
        ranking = []
        for e in entradas:
            count = approved_counts.get(e.id, 0)
            if count > 0:
                ranking.append({
                    "padron_id": e.id,
                    "nombre": e.nombre,
                    "apellido": e.apellidos,
                    "actividades_aprobadas": count
                })
        ranking.sort(key=lambda x: x["actividades_aprobadas"], reverse=True)
        return ranking

    async def obtener_reporte_rapido(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        current_user: CurrentUser,
        docente_id: Optional[UUID] = None
    ) -> dict:
        docente_filter = await self._check_access_and_get_docente_filter(current_user, materia_id, docente_id)
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            raise ValueError("No existe un padrón activo para la materia y cohorte especificadas.")
            
        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        calificaciones = await self.calif_repo.get_calificaciones_by_materia(materia_id, docente_filter)
        
        total_alumnos = len(entradas)
        total_calificaciones = len(calificaciones)
        aprobadas = sum(1 for c in calificaciones if c.aprobado)
        tasa_aprobacion = (aprobadas / total_calificaciones * 100) if total_calificaciones > 0 else 0.0
        
        return {
            "total_alumnos": total_alumnos,
            "total_calificaciones": total_calificaciones,
            "tasa_aprobacion": tasa_aprobacion
        }

    async def obtener_notas_finales(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        current_user: CurrentUser,
        docente_id: Optional[UUID] = None
    ) -> List[dict]:
        docente_filter = await self._check_access_and_get_docente_filter(current_user, materia_id, docente_id)
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            raise ValueError("No existe un padrón activo para la materia y cohorte especificadas.")
            
        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        calificaciones = await self.calif_repo.get_calificaciones_by_materia(materia_id, docente_filter)
        
        calif_by_student = {}
        for c in calificaciones:
            if c.entrada_padron_id not in calif_by_student:
                calif_by_student[c.entrada_padron_id] = []
            calif_by_student[c.entrada_padron_id].append(c)
            
        res = []
        for e in entradas:
            student_califs = calif_by_student.get(e.id, [])
            grades_map = {}
            for c in student_califs:
                grades_map[c.actividad] = {
                    "nota": c.nota_numerica if c.es_numerica else c.nota_textual,
                    "aprobado": c.aprobado
                }
            res.append({
                "padron_id": e.id,
                "nombre": e.nombre,
                "apellido": e.apellidos,
                "calificaciones": grades_map
            })
        return res

    async def obtener_tps_sin_corregir(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        current_user: CurrentUser,
        docente_id: Optional[UUID] = None
    ) -> List[dict]:
        docente_filter = await self._check_access_and_get_docente_filter(current_user, materia_id, docente_id)
        ungraded = await self.calif_repo.get_ungraded_textual_calificaciones(materia_id, docente_filter)
        
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            raise ValueError("No existe un padrón activo para la materia y cohorte especificadas.")
            
        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        entradas_map = {e.id: e for e in entradas}
        
        res = []
        for c in ungraded:
            e = entradas_map.get(c.entrada_padron_id)
            if e:
                res.append({
                    "padron_id": e.id,
                    "nombre": e.nombre,
                    "apellido": e.apellidos,
                    "actividad": c.actividad,
                    "importado_at": c.importado_at
                })
        return res

    async def obtener_monitor_general(
        self,
        current_user: CurrentUser,
        materia_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        regional: Optional[str] = None,
        comision: Optional[str] = None,
        search: Optional[str] = None,
        estado_actividad: Optional[str] = None,
        desde_fecha: Optional[datetime] = None,
        hasta_fecha: Optional[datetime] = None
    ) -> List[dict]:
        docente_filter = None
        if materia_id:
            docente_filter = await self._check_access_and_get_docente_filter(current_user, materia_id, None)
            
        if not materia_id or not cohorte_id:
            return []
            
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            return []
            
        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        
        if regional:
            entradas = [e for e in entradas if e.regional == regional]
        if comision:
            entradas = [e for e in entradas if e.comision == comision]
        if search:
            search_lower = search.lower()
            entradas = [e for e in entradas if search_lower in e.nombre.lower() or search_lower in e.apellidos.lower() or search_lower in e.email.lower()]
            
        calificaciones = await self.calif_repo.get_calificaciones_by_materia(materia_id, docente_filter)
        
        calif_map = {}
        for c in calificaciones:
            if desde_fecha and c.importado_at and c.importado_at < desde_fecha:
                continue
            if hasta_fecha and c.importado_at and c.importado_at > hasta_fecha:
                continue
            calif_map[(c.entrada_padron_id, c.actividad)] = c
            
        distinct_activities = await self.calif_repo.get_distinct_activities(materia_id, docente_filter)
        
        res = []
        for e in entradas:
            for act in distinct_activities:
                c = calif_map.get((e.id, act))
                status = "Faltante"
                nota = None
                
                if c and c.finalizado:
                    nota = c.nota_numerica if c.es_numerica else c.nota_textual
                    status = "Aprobado" if c.aprobado else "Desaprobado"
                    
                if estado_actividad and status != estado_actividad:
                    continue
                    
                res.append({
                    "padron_id": e.id,
                    "nombre": e.nombre,
                    "apellido": e.apellidos,
                    "actividad": act,
                    "estado": status,
                    "nota": nota,
                    "importado_at": c.importado_at if c else None
                })
        return res
