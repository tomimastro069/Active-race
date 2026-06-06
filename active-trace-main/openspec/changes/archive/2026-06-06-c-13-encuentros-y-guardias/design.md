# Design: C-13 Encuentros y Guardias

## Technical Approach

El enfoque técnico implementa dos dominios completamente separados en la capa de Clean Architecture para `Encuentros` y `Guardias`. 
La capa de base de datos usará SQLAlchemy 2.0. Las entidades `SlotEncuentro`, `InstanciaEncuentro` y `Guardia` heredarán del mixin `TimestampedTenant` garantizando el aislamiento (tenant_id) implícito de los registros.
La lógica para calcular las instancias de un encuentro recurrente recaerá exclusivamente en `EncuentroService`, y se expondrán endpoints REST en FastAPI asegurados con el dependency/guard `require_permission("encuentros:gestionar")`.

## Architecture Decisions

### Decision: Relación Slot e Instancia (Recurrencia vs Evento Único)

**Choice**: Utilizar dos tablas `SlotEncuentro` e `InstanciaEncuentro`. `InstanciaEncuentro` tiene una FK `slot_id` que es nula para "encuentros únicos" y obligatoria para "recurrentes".
**Alternatives considered**: Usar una sola tabla duplicando datos de recurrencia, o usar un modelo genérico de `Eventos`.
**Rationale**: Mantener el patrón de la KB. Un `SlotEncuentro` retiene el patrón de diseño (ej. "todos los lunes por 4 semanas"). F6.2 permite crear instancias únicas sin contaminar la DB con "slots fantasmas".

### Decision: Aislamiento Lógico de Guardias

**Choice**: Crear un dominio completo e independiente para `Guardia`.
**Alternatives considered**: Unificar con `InstanciaEncuentro` usando un campo de "tipo_evento".
**Rationale**: Encuentros y Guardias tienen ciclos de vida, datos requeridos y propósitos muy diferentes. `Guardia` refiere a disponibilidad de tutorías (usa `carrera_id`, `cohorte_id`) mientras que `InstanciaEncuentro` tiene grabaciones, urls de meet y depende de `SlotEncuentro`. Unificarlos violaría el principio de responsabilidad única.

## Data Flow

```text
HTTP Request (POST /encuentros/recurrentes)
  │
  ├── Router (Validación Pydantic + RBAC Guard)
  │
  ├── Service (Generación de fechas N semanas: datetime)
  │
  ├── Repository (SQLAlchemy session + tenant_id implícito)
  │
  └── Database (Alembic Migration applied)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/encuentro.py` | Create | Modelos `SlotEncuentro` e `InstanciaEncuentro` |
| `backend/app/models/guardia.py` | Create | Modelo `Guardia` |
| `backend/app/schemas/encuentro.py` | Create | Schemas de validación in/out (Pydantic) |
| `backend/app/schemas/guardia.py` | Create | Schemas Pydantic para guardias |
| `backend/app/repositories/encuentro_repository.py` | Create | Data access con filtrado tenant_id |
| `backend/app/repositories/guardia_repository.py` | Create | Data access para guardias |
| `backend/app/services/encuentro_service.py` | Create | Core de negocio: `crear_recurrencia` y cálculos de fecha |
| `backend/app/services/guardia_service.py` | Create | Registro de guardias |
| `backend/app/api/routers/encuentros.py` | Create | Endpoints `/api/encuentros/*` |
| `backend/app/api/routers/guardias.py` | Create | Endpoints `/api/guardias/*` |
| `backend/app/main.py` | Modify | Registrar routers nuevos (`include_router`) |
| `backend/alembic/versions/XXX.py` | Create | Migración de base de datos (`alembic revision --autogenerate`) |

## Interfaces / Contracts

```python
# Ejemplo: Payload para la creación de encuentro recurrente
class SlotEncuentroCreate(BaseModel):
    materia_id: UUID4
    titulo: str
    hora: time
    dia_semana: DiaSemanaEnum
    fecha_inicio: date
    cant_semanas: int = Field(ge=1, le=52)
    meet_url: str

class InstanciaEncuentroUpdate(BaseModel):
    estado: EstadoEncuentroEnum
    meet_url: str | None
    video_url: str | None
    comentario: str | None
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Lógica de cálculo de fechas de `EncuentroService` | Mockear repositorios; probar bisiestos y saltos de mes. |
| Integration | Repositories (`Encuentro` y `Guardia`) | Crear y leer asegurando que `tenant_id` filtra correctamente. |
| E2E | Endpoints `/api/encuentros` y `/api/guardias` | Requests con un token válido asegurando que `403` aplica sin permisos. |

## Migration / Rollout

No data migration from external systems required. Standard Alembic migration for new tables.

## Open Questions

- [ ] Ninguna.
