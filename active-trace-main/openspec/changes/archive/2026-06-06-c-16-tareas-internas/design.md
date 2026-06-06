# Design: Tareas Internas

## Technical Approach

The `tareas-internas` capability will provide a robust backend structure to track, assign, and communicate on tasks within a tenant context. Following the proposal, we will implement SQLAlchemy 2.0 async models (`Tarea` and `ComentarioTarea`) inheriting from `TimestampedTenant` for automatic tenant isolation. Data access will be channeled through `TareaRepository` and `ComentarioTareaRepository`, which inherit from `BaseRepository` to ensure query scoping. A dedicated `TareaService` will enforce state transitions and business logic, while the `/api/v1/tareas` router will expose endpoints protected by `require_permission`.

## Architecture Decisions

### Decision: State Management Enum

**Choice**: Use Python's `Enum` (`EstadoTareaEnum`) to represent task states (`PENDIENTE`, `EN_PROGRESO`, `RESUELTA`, `CANCELADA`) and map it to an SQLAlchemy `Enum` column.
**Alternatives considered**: String columns with application-level validation or a separate dictionary lookup table.
**Rationale**: Native DB Enums provide strict database-level constraints and integrate seamlessly with SQLAlchemy and Pydantic, making validation automatic at the API and DB layers.

### Decision: Context Linking

**Choice**: Make `contexto_id` an unconstrained `UUID` column instead of a strict foreign key.
**Alternatives considered**: Strict foreign keys linking to specific tables (e.g., `Evaluacion`, `Aviso`), or polymorphic relationships.
**Rationale**: An unconstrained UUID allows tasks to be linked to *any* entity in the system without requiring schema changes or complex polymorphic mapping. This flexibility is ideal for internal tasks that might refer to various modules.

### Decision: Comment Threading

**Choice**: A flat comment list associated with a task (`tarea_id`), ordered by `created_at`.
**Alternatives considered**: Nested/hierarchical comments.
**Rationale**: A flat list is simpler to implement, faster to query, and sufficient for task-oriented communication threads.

## Data Flow

```text
Client Request ──→ APIRouter (/tareas) ──→ TareaService ──→ TareaRepository
     (Auth & DB session via dependencies)                     │
                                                              │
                                                        BaseRepository 
                                                        (Tenant Scope)
                                                              │
                                                           Database
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/tarea.py` | Create | Contains `EstadoTareaEnum`, `Tarea`, and `ComentarioTarea` models inheriting from `TimestampedTenant`. |
| `backend/app/models/__init__.py` | Modify | Export new models. |
| `backend/app/repositories/tarea_repository.py` | Create | `TareaRepository` and `ComentarioTareaRepository` inheriting from `BaseRepository`. |
| `backend/app/repositories/__init__.py` | Modify | Export new repositories. |
| `backend/app/schemas/tarea.py` | Create | Pydantic models for creation, update, and response DTOs. |
| `backend/app/services/tarea_service.py` | Create | Service handling task creation, state transitions, comment additions, and permission checks for `gestionar_propio`. |
| `backend/app/api/v1/routers/tareas.py` | Create | Endpoints: `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `POST /{id}/comentarios`, `GET /{id}/comentarios`. |
| `backend/app/main.py` | Modify | Include the `tareas.py` router under `/api/v1`. |
| `backend/alembic/versions/*_tareas.py` | Create | Migration script for the new tables. |

## Interfaces / Contracts

### Tarea Models

```python
import enum
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampedTenant

class EstadoTareaEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"

class Tarea(TimestampedTenant):
    __tablename__ = "tareas"
    
    materia_id = Column(UUID(as_uuid=True), nullable=True)
    asignado_a = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    asignado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    estado = Column(Enum(EstadoTareaEnum), default=EstadoTareaEnum.PENDIENTE, nullable=False)
    descripcion = Column(String, nullable=False)
    contexto_id = Column(UUID(as_uuid=True), nullable=True)
    
    comentarios = relationship("ComentarioTarea", back_populates="tarea", cascade="all, delete-orphan")

class ComentarioTarea(TimestampedTenant):
    __tablename__ = "comentarios_tarea"
    
    tarea_id = Column(UUID(as_uuid=True), ForeignKey("tareas.id"), nullable=False)
    autor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    texto = Column(String, nullable=False)
    
    tarea = relationship("Tarea", back_populates="comentarios")
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | State transitions and permission logic. | Test `TareaService` methods directly to ensure invalid transitions raise errors and `gestionar_propio` correctly restricts read/write access to assigned tasks. |
| Integration | API routes and Tenant Isolation. | Use `AsyncClient` in `tests/api/test_tareas_api.py`. Inject `{"Authorization": "Bearer mock-token"}` headers to bypass `TenantMiddleware` 401s. Verify that a user in Tenant A cannot see or modify tasks in Tenant B. |

## Migration / Rollout

No complex data migration required. A standard Alembic migration will create the `tareas` and `comentarios_tarea` tables.

## Open Questions

- None
