from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.tarea import EstadoTareaEnum

class ComentarioTareaBase(BaseModel):
    texto: str

class ComentarioTareaCreate(ComentarioTareaBase):
    pass

class ComentarioTareaResponse(ComentarioTareaBase):
    id: UUID
    tarea_id: UUID
    autor_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TareaBase(BaseModel):
    descripcion: str
    materia_id: Optional[UUID] = None
    contexto_id: Optional[UUID] = None

class TareaCreate(TareaBase):
    asignado_a: UUID

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[EstadoTareaEnum] = None

class TareaResponse(TareaBase):
    id: UUID
    asignado_a: UUID
    asignado_por: UUID
    estado: EstadoTareaEnum
    created_at: datetime
    updated_at: datetime
    
    # We won't include all comments in the base task response to avoid huge payloads.
    # Comments will be fetched via a specific endpoint, but we can include a field if needed.
    # For now, keep it simple.
    
    model_config = ConfigDict(from_attributes=True)
