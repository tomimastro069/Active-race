import pytest
from datetime import time
from uuid import uuid4
from app.schemas.guardia import GuardiaCreate, GuardiaResponse
from app.models.guardia import EstadoGuardiaEnum

def test_guardia_create_validation():
    valid_data = {
        "materia_id": uuid4(),
        "asignacion_id": uuid4(),
        "dia_semana": "Lunes",
        "hora_inicio": time(14, 0),
        "hora_fin": time(15, 0)
    }
    schema = GuardiaCreate(**valid_data)
    assert schema.dia_semana == "Lunes"
    assert schema.hora_inicio == time(14, 0)
