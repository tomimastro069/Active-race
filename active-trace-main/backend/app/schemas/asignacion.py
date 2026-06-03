from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class AsignacionBase(BaseModel):
    usuario_id: UUID = Field(..., description="ID del usuario asignado")
    rol_id: UUID = Field(..., description="ID del rol asignado")
    materia_id: Optional[UUID] = Field(None, description="ID de la Materia (opcional)")
    carrera_id: Optional[UUID] = Field(None, description="ID de la Carrera (opcional)")
    cohorte_id: Optional[UUID] = Field(None, description="ID de la Cohorte (opcional)")
    comisiones: Optional[List[str]] = Field(None, description="Lista de comisiones asignadas")
    responsable_id: Optional[UUID] = Field(None, description="ID del usuario coordinador responsable")
    desde: datetime = Field(..., description="Inicio de la vigencia de la asignación")
    hasta: Optional[datetime] = Field(None, description="Fin de la vigencia de la asignación")

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

class AsignacionCreate(AsignacionBase):
    pass

class AsignacionUpdate(BaseModel):
    rol_id: Optional[UUID] = None
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comisiones: Optional[List[str]] = None
    responsable_id: Optional[UUID] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None

    model_config = ConfigDict(
        extra="forbid"
    )

class AsignacionResponse(AsignacionBase):
    id: UUID
    tenant_id: UUID
    estado_vigencia: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class AsignacionMasivaCreate(BaseModel):
    usuario_ids: List[UUID]
    rol_id: UUID
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comisiones: Optional[List[str]] = None
    responsable_id: Optional[UUID] = None
    desde: datetime
    hasta: Optional[datetime] = None

    model_config = ConfigDict(
        extra="forbid"
    )


class EquipoClonarRequest(BaseModel):
    source_materia_id: UUID
    source_cohorte_id: UUID
    target_materia_id: UUID
    target_cohorte_id: UUID
    nuevo_desde: datetime
    nuevo_hasta: Optional[datetime] = None

    model_config = ConfigDict(
        extra="forbid"
    )


class AsignacionVigenciaUpdate(BaseModel):
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None

    model_config = ConfigDict(
        extra="forbid"
    )

