import pytest
from datetime import date, time, datetime
from uuid import uuid4
from pydantic import ValidationError
from app.schemas.encuentro import (
    SlotEncuentroCreate,
    SlotEncuentroResponse,
    InstanciaEncuentroCreate,
    InstanciaEncuentroUpdate,
    InstanciaEncuentroResponse
)
from app.models.encuentro import DiaSemanaEnum, EstadoEncuentroEnum

def test_slot_encuentro_create_validation():
    # Valid data
    valid_data = {
        "materia_id": uuid4(),
        "titulo": "Clase de consulta",
        "hora": time(10, 0),
        "dia_semana": DiaSemanaEnum.LUNES,
        "fecha_inicio": date(2026, 6, 8),
        "cant_semanas": 4,
        "meet_url": "https://meet.google.com/abc-def-ghi"
    }
    schema = SlotEncuentroCreate(**valid_data)
    assert schema.titulo == "Clase de consulta"
    assert schema.cant_semanas == 4

    # Invalid cant_semanas (<1)
    invalid_data = valid_data.copy()
    invalid_data["cant_semanas"] = 0
    with pytest.raises(ValidationError):
        SlotEncuentroCreate(**invalid_data)

    # Invalid cant_semanas (>52)
    invalid_data = valid_data.copy()
    invalid_data["cant_semanas"] = 53
    with pytest.raises(ValidationError):
        SlotEncuentroCreate(**invalid_data)

def test_instancia_encuentro_update():
    valid_update = {
        "estado": EstadoEncuentroEnum.REALIZADO,
        "meet_url": "https://meet.google.com/abc-def-ghi",
        "video_url": "https://drive.google.com/rec",
        "comentario": "Todo bien"
    }
    schema = InstanciaEncuentroUpdate(**valid_update)
    assert schema.estado == EstadoEncuentroEnum.REALIZADO
    assert schema.video_url == "https://drive.google.com/rec"
