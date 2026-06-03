import csv
import codecs
from typing import List, Dict, Tuple, Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.calificacion import CalificacionRepository
from app.repositories.umbral import UmbralMateriaRepository
from app.repositories.padron_repository import PadronRepository
from app.repositories.asignacion import AsignacionRepository
from app.services.audit import AuditService
from app.models.asignacion import Asignacion
from app.core.security import generate_email_hash
from app.schemas.calificacion import CalificacionPreviewResponse, CalificacionImportResponse

class CalificacionService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.calif_repo = CalificacionRepository(db, tenant_id)
        self.umbral_repo = UmbralMateriaRepository(db, tenant_id)
        self.padron_repo = PadronRepository(db, tenant_id)
        self.asignacion_repo = AsignacionRepository(Asignacion, db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    def _get_email_from_row(self, row: dict) -> str:
        possible_keys = [
            'email', 'direccion de correo', 'email address', 'correo',
            'dirección de correo electrónico', 'dirección de correo',
            'correo electrónico', 'correo electronico'
        ]
        for key, val in row.items():
            if key.lower().strip() in possible_keys:
                return val.strip()
        return ""

    def _is_metadata_column(self, col_name: str) -> bool:
        normalized = col_name.lower().strip()
        metadata_keywords = [
            'email', 'direccion de correo', 'email address', 'correo',
            'dirección de correo electrónico', 'dirección de correo',
            'correo electrónico', 'correo electronico', 'nombre', 'nombre completo',
            'first name', 'last name', 'apellidos', 'comision', 'regional',
            'usuario_id', 'id', 'institución', 'departamento', 'id number',
            'número de id', 'comisión', 'estado', 'último acceso', 'institucion'
        ]
        return normalized in metadata_keywords or not normalized

    async def _get_threshold_config(
        self,
        docente_id: UUID,
        materia_id: UUID
    ) -> Tuple[int, List[str]]:
        """
        Retrieves the active threshold config for the teacher and subject.
        Falls back to default values if not configured.
        """
        default_pct = 60
        default_valores = ["Satisfactorio", "Supera lo esperado"]

        # Find active assignment for the docente and materia
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

    async def preview_csv(self, file_content: str) -> CalificacionPreviewResponse:
        """
        Parses CSV headers and first few rows to provide a preview of activity columns.
        """
        lines = file_content.splitlines()
        if not lines:
            raise ValueError("El archivo está vacío.")

        delimiter = ';' if ';' in lines[0] else ','
        reader = csv.DictReader(lines, delimiter=delimiter)
        
        headers = reader.fieldnames if reader.fieldnames else []
        activity_headers = [h for h in headers if not self._is_metadata_column(h)]
        
        sample_rows = []
        count = 0
        for row in reader:
            sample_row = {
                "email": self._get_email_from_row(row),
            }
            for act in activity_headers:
                sample_row[act] = row.get(act, '')
            sample_rows.append(sample_row)
            count += 1
            if count >= 5:
                break
        
        # Count remaining rows
        total_rows = count
        for _ in reader:
            total_rows += 1

        return CalificacionPreviewResponse(
            headers=activity_headers,
            rows=sample_rows,
            estimated_grades_count=total_rows * len(activity_headers)
        )

    async def importar_calificaciones_csv(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        docente_id: UUID,
        file_content: str
    ) -> CalificacionImportResponse:
        """
        Parses CSV, evaluates approval using the teacher's active threshold,
        and performs bulk upsert.
        """
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            raise ValueError("No existe un padrón activo para la materia y cohorte especificadas.")

        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        # Map email_hash -> EntradaPadron.id
        email_map = {e.email_hash: e.id for e in entradas}

        lines = file_content.splitlines()
        if not lines:
            raise ValueError("El archivo está vacío.")

        delimiter = ';' if ';' in lines[0] else ','
        reader = csv.DictReader(lines, delimiter=delimiter)

        headers = reader.fieldnames if reader.fieldnames else []
        activity_headers = [h for h in headers if not self._is_metadata_column(h)]

        if not activity_headers:
            raise ValueError("No se encontraron columnas de actividades o calificaciones en el archivo CSV.")

        # Get threshold configuration
        umbral_pct, valores_aprobatorios = await self._get_threshold_config(docente_id, materia_id)

        calificaciones_to_upsert = []
        unmatched_emails = []
        import_time = datetime.utcnow()

        for row in reader:
            email = self._get_email_from_row(row)
            if not email:
                continue

            email_hash = generate_email_hash(email)
            entrada_padron_id = email_map.get(email_hash)

            if not entrada_padron_id:
                if email not in unmatched_emails:
                    unmatched_emails.append(email)
                continue

            for act in activity_headers:
                raw_val = row.get(act, '')
                if raw_val is None or raw_val.strip() == '':
                    continue

                act_clean = act.strip()
                is_numeric = act_clean.lower().endswith("(real)")

                nota_numerica = None
                nota_textual = None
                aprobado = False

                if is_numeric:
                    try:
                        clean_num = raw_val.replace(',', '.').strip()
                        nota_numerica = float(clean_num)
                        aprobado = nota_numerica >= umbral_pct
                    except ValueError:
                        is_numeric = False
                        nota_textual = raw_val.strip()
                        aprobado = nota_textual in valores_aprobatorios
                else:
                    nota_textual = raw_val.strip()
                    aprobado = nota_textual in valores_aprobatorios

                calificaciones_to_upsert.append({
                    "entrada_padron_id": entrada_padron_id,
                    "actividad": act_clean,
                    "nota_numerica": nota_numerica,
                    "nota_textual": nota_textual,
                    "aprobado": aprobado,
                    "finalizado": True,
                    "es_numerica": is_numeric,
                    "origen": "Importado",
                    "importado_at": import_time
                })

        imported_count = 0
        if calificaciones_to_upsert:
            imported_count = await self.calif_repo.bulk_upsert_calificaciones(
                materia_id=materia_id,
                docente_id=docente_id,
                calificaciones_data=calificaciones_to_upsert
            )

        # Audit action
        await self.audit_service.log_action(
            actor_id=docente_id,
            accion="CALIFICACIONES_IMPORTAR",
            materia_id=materia_id,
            detalle={
                "cohorte_id": str(cohorte_id),
                "total_calificaciones": imported_count,
                "no_emparejados": len(unmatched_emails)
            },
            filas_afectadas=imported_count
        )

        return CalificacionImportResponse(
            imported_count=imported_count,
            unmatched_emails=unmatched_emails
        )

    async def importar_finalizaciones_csv(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        docente_id: UUID,
        file_content: str
    ) -> CalificacionImportResponse:
        """
        Parses completion report CSV. Updates existing grades to finalizado=True,
        or creates new qualitative ungraded grades with finalizado=True.
        """
        active_version = await self.padron_repo.get_active_version(materia_id, cohorte_id)
        if not active_version:
            raise ValueError("No existe un padrón activo para la materia y cohorte especificadas.")

        entradas = await self.padron_repo.get_entradas_by_version(active_version.id)
        email_map = {e.email_hash: e.id for e in entradas}

        lines = file_content.splitlines()
        if not lines:
            raise ValueError("El archivo está vacío.")

        delimiter = ';' if ';' in lines[0] else ','
        reader = csv.DictReader(lines, delimiter=delimiter)

        headers = reader.fieldnames if reader.fieldnames else []
        activity_headers = [h for h in headers if not self._is_metadata_column(h)]

        if not activity_headers:
            raise ValueError("No se encontraron columnas de actividades en el archivo CSV de finalizaciones.")

        calificaciones_to_upsert = []
        unmatched_emails = []
        import_time = datetime.utcnow()

        not_completed_strs = ["no", "incompleto", "no completado", "no finalizado", "0", "false"]

        for row in reader:
            email = self._get_email_from_row(row)
            if not email:
                continue

            email_hash = generate_email_hash(email)
            entrada_padron_id = email_map.get(email_hash)

            if not entrada_padron_id:
                if email not in unmatched_emails:
                    unmatched_emails.append(email)
                continue

            for act in activity_headers:
                raw_val = row.get(act, '')
                val_clean = raw_val.strip().lower()
                
                if not val_clean or val_clean in not_completed_strs:
                    continue

                act_clean = act.strip()
                existing = await self.calif_repo.get_calificacion(
                    entrada_padron_id=entrada_padron_id,
                    materia_id=materia_id,
                    docente_id=docente_id,
                    actividad=act_clean
                )

                if existing:
                    calificaciones_to_upsert.append({
                        "entrada_padron_id": entrada_padron_id,
                        "actividad": act_clean,
                        "nota_numerica": existing.nota_numerica,
                        "nota_textual": existing.nota_textual,
                        "aprobado": existing.aprobado,
                        "finalizado": True,
                        "es_numerica": existing.es_numerica,
                        "origen": existing.origen,
                        "importado_at": existing.importado_at
                    })
                else:
                    calificaciones_to_upsert.append({
                        "entrada_padron_id": entrada_padron_id,
                        "actividad": act_clean,
                        "nota_numerica": None,
                        "nota_textual": None,
                        "aprobado": False,
                        "finalizado": True,
                        "es_numerica": False,
                        "origen": "Importado",
                        "importado_at": import_time
                    })

        imported_count = 0
        if calificaciones_to_upsert:
            imported_count = await self.calif_repo.bulk_upsert_calificaciones(
                materia_id=materia_id,
                docente_id=docente_id,
                calificaciones_data=calificaciones_to_upsert
            )

        # Audit action
        await self.audit_service.log_action(
            actor_id=docente_id,
            accion="FINALIZACIONES_IMPORTAR",
            materia_id=materia_id,
            detalle={
                "cohorte_id": str(cohorte_id),
                "total_finalizaciones": imported_count,
                "no_emparejados": len(unmatched_emails)
            },
            filas_afectadas=imported_count
        )

        return CalificacionImportResponse(
            imported_count=imported_count,
            unmatched_emails=unmatched_emails
        )

    async def vaciar_calificaciones(
        self,
        materia_id: UUID,
        docente_id: UUID
    ) -> int:
        """
        Logically deletes all grades for a subject imported by the given teacher.
        """
        deleted_count = await self.calif_repo.vaciar_calificaciones(materia_id, docente_id)
        
        # Audit action
        await self.audit_service.log_action(
            actor_id=docente_id,
            accion="CALIFICACIONES_VACIAR",
            materia_id=materia_id,
            detalle={},
            filas_afectadas=deleted_count
        )
        return deleted_count

    async def configurar_umbral(
        self,
        docente_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: Optional[List[str]] = None
    ) -> Any:
        """
        Configures the custom threshold for the teacher and subject.
        """
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
            raise ValueError("El docente no tiene una asignación vigente para la materia especificada.")

        umbral = await self.umbral_repo.upsert_umbral(
            asignacion_id=active_assignment.id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios
        )

        # Audit action
        await self.audit_service.log_action(
            actor_id=docente_id,
            accion="UMBRAL_CONFIGURAR",
            materia_id=materia_id,
            detalle={
                "umbral_pct": umbral_pct,
                "valores_aprobatorios": valores_aprobatorios
            },
            filas_afectadas=1
        )
        return umbral

    async def get_umbral(
        self,
        docente_id: UUID,
        materia_id: UUID
    ) -> Optional[Any]:
        """
        Retrieves the configured threshold for the teacher and subject.
        """
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
            return None

        return await self.umbral_repo.get_by_asignacion_y_materia(
            asignacion_id=active_assignment.id,
            materia_id=materia_id
        )
