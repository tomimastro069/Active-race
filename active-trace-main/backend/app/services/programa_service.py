from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.programa import ProgramaMateria
from app.repositories.programa import ProgramaRepository
from app.services.audit import AuditService


class ProgramaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = ProgramaRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    async def subir_programa(
        self,
        *,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        titulo: str,
        filename: str,
        content_type: str,
        contenido: bytes,
        actor_id: UUID,
    ) -> ProgramaMateria:
        programa = ProgramaMateria(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            titulo=titulo,
            filename=filename,
            content_type=content_type or "application/pdf",
            file_size=len(contenido),
            contenido=contenido,
        )
        programa = await self.repo.create(programa)
        await self.db.flush()
        await self.audit_service.log_action(
            actor_id=actor_id,
            accion="PROGRAMA_SUBIR",
            materia_id=materia_id,
            detalle={"id": str(programa.id), "titulo": titulo, "filename": filename},
        )
        return programa

    async def listar_programas(
        self,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
    ) -> List[ProgramaMateria]:
        return await self.repo.list_programas(materia_id, carrera_id, cohorte_id)

    async def get_programa(self, programa_id: UUID) -> Optional[ProgramaMateria]:
        return await self.repo.get_by_id(programa_id)

    async def reemplazar_programa(
        self,
        *,
        programa_id: UUID,
        titulo: str,
        filename: str,
        content_type: str,
        contenido: bytes,
        actor_id: UUID,
    ) -> ProgramaMateria:
        """Reemplaza un programa: soft-delete del anterior + alta nueva (append-only)."""
        anterior = await self.repo.get_by_id(programa_id)
        if anterior is None:
            raise ValueError("Programa no encontrado o pertenece a otro tenant.")

        nuevo = await self.subir_programa(
            materia_id=anterior.materia_id,
            carrera_id=anterior.carrera_id,
            cohorte_id=anterior.cohorte_id,
            titulo=titulo,
            filename=filename,
            content_type=content_type,
            contenido=contenido,
            actor_id=actor_id,
        )
        await self.repo.delete_logical(programa_id)
        return nuevo
