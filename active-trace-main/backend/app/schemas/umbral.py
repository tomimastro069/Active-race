from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from typing import List, Optional

class UmbralMateriaConfig(BaseModel):
    umbral_pct: int = Field(60, ge=0, le=100, description="Porcentaje mínimo de aprobación para notas numéricas")
    valores_aprobatorios: Optional[List[str]] = Field(default_factory=lambda: ["Satisfactorio", "Supera lo esperado"], description="Valores cualitativos considerados aprobados")

    model_config = ConfigDict(
        extra="forbid"
    )

class UmbralMateriaResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    asignacion_id: UUID
    materia_id: UUID
    umbral_pct: int
    valores_aprobatorios: Optional[List[str]] = None

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )
