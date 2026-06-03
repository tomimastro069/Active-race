from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.comunicacion import EstadoComunicacion


class DestinatarioItem(BaseModel):
    """Represents a single recipient for a communication."""

    email: EmailStr
    nombre: str
    actividades_faltantes: str = ""

    model_config = ConfigDict(extra="forbid")


class ComunicacionPreviewRequest(BaseModel):
    """Request body for the preview endpoint. No data is persisted."""

    asunto_template: str = Field(..., max_length=500)
    cuerpo_template: str
    variables: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ComunicacionPreviewResponse(BaseModel):
    """Response for the preview endpoint with rendered templates."""

    asunto_renderizado: str
    cuerpo_renderizado: str

    model_config = ConfigDict(extra="forbid")


class ComunicacionEnviarRequest(BaseModel):
    """Request body to enqueue one or more outbound communications."""

    asunto_template: str = Field(..., max_length=500)
    cuerpo_template: str
    destinatarios: list[DestinatarioItem] = Field(..., min_length=1)
    materia_id: UUID

    model_config = ConfigDict(extra="forbid")


class ComunicacionResponse(BaseModel):
    """Response DTO for a Comunicacion row.

    SECURITY: `destinatario` is NEVER included — it contains AES-256 ciphertext PII.
    Only `destinatario_hash` (HMAC-SHA256 hex digest) is exposed.
    """

    id: UUID
    tenant_id: UUID
    enviado_por: UUID
    materia_id: UUID
    destinatario_hash: str
    asunto: str
    cuerpo: str
    estado: EstadoComunicacion
    lote_id: Optional[UUID] = None
    aprobado: bool
    enviado_at: Optional[datetime] = None
    intentos: int
    max_intentos: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # NOTE: `destinatario` is intentionally absent from this schema.
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class LoteResumenResponse(BaseModel):
    """Aggregate summary for a communication batch."""

    lote_id: UUID
    total: int
    por_estado: dict[str, int]

    model_config = ConfigDict(extra="forbid")
