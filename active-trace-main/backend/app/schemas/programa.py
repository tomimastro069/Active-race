from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class ProgramaResponse(BaseModel):
    """Metadatos de un programa (sin el binario)."""
    id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    filename: str
    content_type: str
    file_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
