from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.core.dependencies import get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.programa import ProgramaResponse
from app.services.programa_service import ProgramaService

router = APIRouter(prefix="/programas", tags=["programas"])

PDF_CONTENT_TYPE = "application/pdf"


@router.post("/", response_model=ProgramaResponse, status_code=status.HTTP_201_CREATED)
async def subir_programa(
    materia_id: UUID = Form(...),
    carrera_id: UUID = Form(...),
    cohorte_id: UUID = Form(...),
    titulo: str = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Sube el programa oficial (PDF) de una materia por carrera y cohorte (HU-23)."""
    if file.content_type not in (PDF_CONTENT_TYPE, "application/octet-stream"):
        raise HTTPException(status_code=415, detail="El programa debe ser un archivo PDF.")
    contenido = await file.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    service = ProgramaService(db, current_user.tenant_id)
    programa = await service.subir_programa(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        titulo=titulo,
        filename=file.filename or "programa.pdf",
        content_type=PDF_CONTENT_TYPE,
        contenido=contenido,
        actor_id=current_user.id,
    )
    await db.commit()
    await db.refresh(programa)
    return programa


@router.get("/", response_model=List[ProgramaResponse])
async def listar_programas(
    materia_id: Optional[UUID] = None,
    carrera_id: Optional[UUID] = None,
    cohorte_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Lista los programas (metadatos), filtrable por materia/carrera/cohorte (HU-23)."""
    service = ProgramaService(db, current_user.tenant_id)
    return await service.listar_programas(materia_id, carrera_id, cohorte_id)


@router.get("/{programa_id}/download")
async def descargar_programa(
    programa_id: UUID,
    current_user: CurrentUser = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Descarga el PDF de un programa (HU-23)."""
    service = ProgramaService(db, current_user.tenant_id)
    programa = await service.get_programa(programa_id)
    if programa is None:
        raise HTTPException(status_code=404, detail="Programa no encontrado.")
    return Response(
        content=programa.contenido,
        media_type=programa.content_type,
        headers={"Content-Disposition": f'attachment; filename="{programa.filename}"'},
    )


@router.put("/{programa_id}", response_model=ProgramaResponse)
async def reemplazar_programa(
    programa_id: UUID,
    titulo: str = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_permission("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Reemplaza un programa existente conservando el histórico (HU-23)."""
    if file.content_type not in (PDF_CONTENT_TYPE, "application/octet-stream"):
        raise HTTPException(status_code=415, detail="El programa debe ser un archivo PDF.")
    contenido = await file.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    service = ProgramaService(db, current_user.tenant_id)
    try:
        nuevo = await service.reemplazar_programa(
            programa_id=programa_id,
            titulo=titulo,
            filename=file.filename or "programa.pdf",
            content_type=PDF_CONTENT_TYPE,
            contenido=contenido,
            actor_id=current_user.id,
        )
        await db.commit()
        await db.refresh(nuevo)
        return nuevo
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
