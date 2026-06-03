from pydantic import BaseModel, ConfigDict, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class UsuarioBase(BaseModel):
    email: EmailStr = Field(..., description="Email del usuario")
    nombre: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    estado: str = Field("Activo", description="Estado del usuario: Activo o Inactivo")
    dni: Optional[str] = Field(None, max_length=50)
    cuil: Optional[str] = Field(None, max_length=50)
    cbu: Optional[str] = Field(None, max_length=50)
    alias_cbu: Optional[str] = Field(None, max_length=100)
    banco: Optional[str] = Field(None, max_length=100)
    regional: Optional[str] = Field(None, max_length=100)
    legajo: Optional[str] = Field(None, max_length=50)
    legajo_profesional: Optional[str] = Field(None, max_length=50)
    facturador: bool = Field(False)

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    estado: Optional[str] = "Activo"
    dni: Optional[str] = None
    cuil: Optional[str] = None
    cbu: Optional[str] = None
    alias_cbu: Optional[str] = None
    banco: Optional[str] = None
    regional: Optional[str] = None
    legajo: Optional[str] = None
    legajo_profesional: Optional[str] = None
    facturador: Optional[bool] = False

    model_config = ConfigDict(
        extra="forbid"
    )

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    estado: Optional[str] = None
    dni: Optional[str] = None
    cuil: Optional[str] = None
    cbu: Optional[str] = None
    alias_cbu: Optional[str] = None
    banco: Optional[str] = None
    regional: Optional[str] = None
    legajo: Optional[str] = None
    legajo_profesional: Optional[str] = None
    facturador: Optional[bool] = None

    model_config = ConfigDict(
        extra="forbid"
    )

class UsuarioResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    nombre: Optional[str]
    apellidos: Optional[str]
    estado: str
    dni: Optional[str] = None
    cuil: Optional[str] = None
    cbu: Optional[str] = None
    alias_cbu: Optional[str] = None
    banco: Optional[str] = None
    regional: Optional[str] = None
    legajo: Optional[str] = None
    legajo_profesional: Optional[str] = None
    facturador: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
