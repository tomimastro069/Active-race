# Design: C-11 analisis-atrasados-reportes

## Technical Approach

We will encapsulate all Epic 2 (F2.2–F2.9) reporting logic in a new `AnalisisService` layer. To keep services free of direct SQLAlchemy manipulation and abide by the repository pattern, we will extend `CalificacionRepository` and `PadronRepository` with specific data retrieval helpers. A new API router, `analisis`, will expose REST endpoints corresponding to the required UI monitors and exports, enforcing the `atrasados:ver` and `atrasados:ver_propio` RBAC boundaries.

## Architecture Decisions

### Decision: In-Memory vs DB-side Grouping for Rankings

**Choice**: DB-side grouping via Repository queries.
**Alternatives considered**: Fetching all raw `Calificacion` objects and grouping them in Python (`AnalisisService`).
**Rationale**: Fetching all data to memory scales poorly with large cohorts and multiple activities. Pushing the aggregation (`GROUP BY`, `COUNT`) down to the repository leveraging SQLAlchemy's func ensures high performance and reduced memory overhead. The service will receive pre-aggregated rows.

### Decision: Separating Analytics from Core Calificaciones Router

**Choice**: A dedicated `/api/v1/analisis/` router and `AnalisisService`.
**Alternatives considered**: Appending new endpoints to `calificacion_router` and logic to `CalificacionService`.
**Rationale**: The analytics features span across `Calificacion`, `Padron`, and `UmbralMateria` domains. Overloading the base `CalificacionService` would violate single responsibility and bloat the file. A dedicated analytics vertical keeps code boundaries clean.

## Data Flow

    [Client (UI)]
         │ (HTTP GET with query filters)
         ▼
    [API Router: analisis] ── (Validates RBAC & Schemas) ──┐
         │                                                 │
         ▼                                                 ▼
    [AnalisisService] ────────────────────────► [calificacion / padron Repositories]
         │ (Business Logic RN-06 to RN-09)                 │ (Executes optimized SQL)
         ▼                                                 ▼
    [Returns formatted DTOs / CSV] ◄──────────────── [Database]

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/api/v1/routers/analisis.py` | Create | New endpoints for reports and monitors |
| `backend/app/services/analisis_service.py` | Create | Business logic for metrics and ranking |
| `backend/app/schemas/analisis.py` | Create | Pydantic response models |
| `backend/app/repositories/calificacion.py` | Modify | Add DB-side grouping helpers and ungraded TPs query |
| `backend/app/main.py` | Modify | Include the new `analisis` router |
| `backend/tests/test_analisis_service.py` | Create | Strict TDD tests for business rules |
| `backend/tests/api/test_analisis_api.py` | Create | API integration tests |

## Interfaces / Contracts

```python
# backend/app/schemas/analisis.py

class AlumnoAtrasadoResponse(BaseModel):
    padron_id: UUID
    nombre: str
    apellido: str
    actividad: str
    motivo: str # "Faltante" or "Nota menor al umbral"

class RankingResponse(BaseModel):
    padron_id: UUID
    nombre: str
    apellido: str
    actividades_aprobadas: int
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `AnalisisService` (RN-06, RN-09) | Mock repositories; assert logic excludes 0 approvals and identifies thresholds accurately. |
| Integration | API Router + Repositories | Use test DB to insert dummy students and qualifications. Assert HTTP 200 and exact JSON shapes. |

## Migration / Rollout

No migration required. The feature purely reads from existing tables without altering the database schema.

## Open Questions

- [ ] None at the moment. All business rules map to existing DB structures.
