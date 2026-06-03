from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any

class CalificacionResponse(BaseModel):
    id: UUID
    entrada_padron_id: UUID
    materia_id: UUID
    docente_id: UUID
    actividad: str
    nota_numerica: Optional[float] = None
    nota_textual: Optional[str] = None
    aprobado: bool
    finalizado: bool
    es_numerica: bool
    origen: str
    importado_at: Optional[datetime] = None

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

class CalificacionPreviewResponse(BaseModel):
    headers: List[str] = Field(..., description="Headers found in the CSV file")
    rows: List[dict] = Field(..., description="Sample rows (up to 5) for preview")
    estimated_grades_count: int = Field(..., description="Estimated total number of grades that will be imported")

    model_config = ConfigDict(
        extra="forbid"
    )

class CalificacionImportResponse(BaseModel):
    imported_count: int = Field(..., description="Number of grades successfully imported")
    unmatched_emails: List[str] = Field(..., description="List of emails in the CSV that did not match the active padron")

    model_config = ConfigDict(
        extra="forbid"
    )

class CalificacionVaciarRequest(BaseModel):
    materia_id: UUID = Field(..., description="ID de la materia para vaciar calificaciones")

    model_config = ConfigDict(
        extra="forbid"
    )

class UmbralConfigPayload(BaseModel):
    materia_id: UUID = Field(..., description="ID de la materia")
    umbral_pct: int = Field(60, ge=0, le=100, description="Porcentaje mínimo de aprobación")
    valores_aprobatorios: Optional[List[str]] = Field(default_factory=lambda: ["Satisfactorio", "Supera lo esperado"], description="Valores cualitativos aprobados")

    model_config = ConfigDict(
        extra="forbid"
    )
