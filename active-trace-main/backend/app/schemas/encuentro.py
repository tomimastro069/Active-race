from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from uuid import UUID
from datetime import date, time, datetime
from typing import Optional
from app.models.encuentro import DiaSemanaEnum, EstadoEncuentroEnum

class SlotEncuentroBase(BaseModel):
    materia_id: UUID
    titulo: str = Field(..., max_length=255)
    hora: time
    dia_semana: DiaSemanaEnum
    fecha_inicio: date
    cant_semanas: int = Field(..., ge=1, le=52)
    meet_url: str = Field(..., max_length=500)

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

class SlotEncuentroCreate(BaseModel):
    materia_id: UUID
    titulo: str = Field(..., max_length=255)
    hora: time
    dia_semana: DiaSemanaEnum
    fecha_inicio: date
    cant_semanas: int = Field(..., ge=1, le=52)
    meet_url: str = Field(..., max_length=500)

    model_config = ConfigDict(
        extra="forbid"
    )

class SlotEncuentroResponse(SlotEncuentroBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class InstanciaEncuentroBase(BaseModel):
    slot_id: Optional[UUID] = None
    materia_id: UUID
    titulo: str = Field(..., max_length=255)
    fecha_hora: datetime
    estado: EstadoEncuentroEnum = EstadoEncuentroEnum.PROGRAMADO
    meet_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    comentario: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

class InstanciaEncuentroCreate(BaseModel):
    materia_id: UUID
    titulo: str = Field(..., max_length=255)
    fecha_hora: datetime
    meet_url: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(
        extra="forbid"
    )

class InstanciaEncuentroUpdate(BaseModel):
    estado: Optional[EstadoEncuentroEnum] = None
    meet_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    comentario: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid"
    )

class InstanciaEncuentroResponse(InstanciaEncuentroBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
