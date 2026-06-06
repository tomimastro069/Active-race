from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import time, datetime
from typing import Optional
from app.models.guardia import EstadoGuardiaEnum

class GuardiaBase(BaseModel):
    materia_id: UUID
    asignacion_id: UUID
    dia_semana: str = Field(..., max_length=100)
    hora_inicio: time
    hora_fin: time

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

class GuardiaCreate(BaseModel):
    materia_id: UUID
    asignacion_id: UUID
    dia_semana: str = Field(..., max_length=100)
    hora_inicio: time
    hora_fin: time

    model_config = ConfigDict(
        extra="forbid"
    )

class GuardiaResponse(GuardiaBase):
    id: UUID
    tenant_id: UUID
    estado: EstadoGuardiaEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
