from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, Dict, Any, List
from datetime import datetime

class AlumnoAtrasadoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    padron_id: UUID
    nombre: str
    apellido: str
    actividad: str
    motivo: str

class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    padron_id: UUID
    nombre: str
    apellido: str
    actividades_aprobadas: int

class ReporteRapidoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    total_alumnos: int
    total_calificaciones: int
    tasa_aprobacion: float

class DetalleNota(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    nota: Optional[Any] = None
    aprobado: bool

class NotasFinalesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    padron_id: UUID
    nombre: str
    apellido: str
    calificaciones: Dict[str, DetalleNota]

class TPSinCorregirResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    padron_id: UUID
    nombre: str
    apellido: str
    actividad: str
    importado_at: Optional[datetime] = None

class MonitorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    padron_id: UUID
    nombre: str
    apellido: str
    actividad: str
    estado: str
    nota: Optional[Any] = None
    importado_at: Optional[datetime] = None
