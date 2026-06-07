from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class ThreadCreate(BaseModel):
    asunto: str = Field(..., max_length=255, description="Asunto de la conversación")
    destinatario_id: UUID = Field(..., description="ID del usuario destinatario")
    mensaje: str = Field(..., description="Cuerpo del primer mensaje")

    model_config = ConfigDict(
        extra="forbid"
    )

class MessageCreate(BaseModel):
    contenido: str = Field(..., description="Contenido de la respuesta")

    model_config = ConfigDict(
        extra="forbid"
    )

class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    remitente_id: UUID
    remitente_nombre: Optional[str] = None
    contenido: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class ThreadResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    asunto: str
    creador_id: UUID
    is_closed: bool
    created_at: datetime
    updated_at: datetime
    miembros: List[UUID]
    mensajes: Optional[List[MessageResponse]] = None

    model_config = ConfigDict(
        from_attributes=True
    )
