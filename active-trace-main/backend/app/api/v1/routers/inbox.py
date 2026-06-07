from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.mensajeria import ThreadCreate, MessageCreate, ThreadResponse, MessageResponse
from app.services.mensajeria import MensajeriaService

router = APIRouter(prefix="/inbox", tags=["inbox"])

@router.get("/threads", response_model=List[ThreadResponse])
async def list_threads(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna la lista de hilos de conversación en los que participa el usuario.
    """
    service = MensajeriaService(db, current_user.tenant_id)
    threads = await service.list_threads(current_user.id)
    return [service.thread_to_response(t) for t in threads]

@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    payload: ThreadCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo hilo de conversación entre el usuario autenticado y otro usuario del mismo tenant.
    """
    service = MensajeriaService(db, current_user.tenant_id)
    try:
        thread = await service.create_thread(
            creador_id=current_user.id,
            asunto=payload.asunto,
            destinatario_id=payload.destinatario_id,
            mensaje_contenido=payload.mensaje
        )
        await db.commit()
        return service.thread_to_response(thread)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/thread/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna el detalle de un hilo de conversación específico, incluyendo sus mensajes,
    solo si el usuario autenticado es miembro del hilo.
    """
    service = MensajeriaService(db, current_user.tenant_id)
    try:
        thread = await service.get_thread(thread_id, current_user.id)
        return service.thread_to_response(thread)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.post("/thread/{thread_id}/reply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def reply_to_thread(
    thread_id: UUID,
    payload: MessageCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permite a un miembro responder a un hilo existente.
    """
    service = MensajeriaService(db, current_user.tenant_id)
    try:
        message = await service.reply_to_thread(
            thread_id=thread_id,
            remitente_id=current_user.id,
            contenido=payload.contenido
        )
        await db.commit()
        return service.message_to_response(message)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
