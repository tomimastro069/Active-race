from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from app.core.dependencies import get_db, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.encuentro import (
    SlotEncuentroCreate,
    SlotEncuentroResponse,
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate
)
from app.services.encuentro_service import EncuentroService

router = APIRouter(prefix="/encuentros", tags=["encuentros"])

@router.post("/recurrentes", status_code=status.HTTP_201_CREATED)
async def crear_recurrente(
    payload: SlotEncuentroCreate,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = EncuentroService(db, current_user.tenant_id)
    try:
        slot, instancias = await service.crear_encuentro_recurrente(payload, actor_id=current_user.id)
        await db.commit()
        return {
            "slot": SlotEncuentroResponse.model_validate(slot),
            "instancias": [InstanciaEncuentroResponse.model_validate(inst) for inst in instancias]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/unicos", response_model=InstanciaEncuentroResponse, status_code=status.HTTP_201_CREATED)
async def crear_unico(
    titulo: str,
    materia_id: UUID,
    fecha_hora: datetime,
    meet_url: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = EncuentroService(db, current_user.tenant_id)
    try:
        instancia = await service.crear_encuentro_unico(
            titulo=titulo,
            materia_id=materia_id,
            fecha_hora=fecha_hora,
            meet_url=meet_url,
            actor_id=current_user.id
        )
        await db.commit()
        return instancia
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/instancias/{instancia_id}", response_model=InstanciaEncuentroResponse)
async def update_instancia(
    instancia_id: UUID,
    payload: InstanciaEncuentroUpdate,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = EncuentroService(db, current_user.tenant_id)
    try:
        instancia = await service.update_instancia(instancia_id, payload, actor_id=current_user.id)
        await db.commit()
        return instancia
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/materias/{materia_id}", response_model=List[InstanciaEncuentroResponse])
async def list_by_materia(
    materia_id: UUID,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = EncuentroService(db, current_user.tenant_id)
    return await service.instancia_repo.list_by_materia(materia_id)

@router.get("/exportar/{materia_id}", response_class=HTMLResponse)
async def exportar_encuentros_html(
    materia_id: UUID,
    current_user: CurrentUser = Depends(require_permission("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db)
):
    service = EncuentroService(db, current_user.tenant_id)
    instancias = await service.instancia_repo.list_by_materia(materia_id)
    # Sort them by date
    instancias.sort(key=lambda x: x.fecha_hora)
    
    html_lines = []
    html_lines.append('<div class="encuentros-virtual-classroom">')
    html_lines.append('  <h3>Clases Sincrónicas</h3>')
    if not instancias:
        html_lines.append('  <p>No hay encuentros programados.</p>')
    else:
        html_lines.append('  <ul>')
        for inst in instancias:
            fecha_str = inst.fecha_hora.strftime("%d/%m/%Y %H:%M")
            link_str = f' - <a href="{inst.meet_url}" target="_blank">Unirse a la clase</a>' if inst.meet_url else ""
            html_lines.append(f'    <li><strong>{inst.titulo}</strong>: {fecha_str}{link_str}</li>')
        html_lines.append('  </ul>')
    html_lines.append('</div>')
    
    return "\n".join(html_lines)
