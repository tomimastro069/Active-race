from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from app.models.evaluacion import EvaluacionTipoEnum, EstadoReservaEnum

class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    evaluacion_id: UUID
    alumno_id: UUID
    fecha_hora: datetime

class ReservaResponse(BaseModel):
    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    fecha_hora: datetime
    estado: EstadoReservaEnum

    model_config = ConfigDict(from_attributes=True)

class EvaluacionResumenResponse(BaseModel):
    """Listado de convocatorias/evaluaciones con contadores (HU-31, HU-24)."""
    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: EvaluacionTipoEnum
    instancia: str
    titulo: Optional[str] = None
    fecha: Optional[date] = None
    dias_disponibles: int
    cupos_totales: int
    convocados: int
    reservas_activas: int
    cupos_disponibles: int

    model_config = ConfigDict(from_attributes=True)

class ConvocadosImport(BaseModel):
    """Padrón de coloquio: alumnos elegibles a convocar (HU-30)."""
    model_config = ConfigDict(extra='forbid')
    alumno_ids: List[UUID]

class ConvocadosImportResponse(BaseModel):
    evaluacion_id: UUID
    convocados_nuevos: int
    convocados_totales: int

class AgendaReservaResponse(BaseModel):
    """Fila de la agenda consolidada de reservas (HU-32)."""
    reserva_id: UUID
    evaluacion_id: UUID
    materia_id: UUID
    instancia: str
    alumno_id: UUID
    alumno_nombre: Optional[str] = None
    fecha_hora: datetime
    estado: EstadoReservaEnum

    model_config = ConfigDict(from_attributes=True)

class ResultadoCreate(BaseModel):
    """Carga de nota final de un alumno en una instancia (HU-33)."""
    model_config = ConfigDict(extra='forbid')
    alumno_id: UUID
    nota_final: str

class ResultadoResponse(BaseModel):
    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    alumno_nombre: Optional[str] = None
    nota_final: str

    model_config = ConfigDict(from_attributes=True)
