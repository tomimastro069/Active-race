# Apply Progress: c-10-calificaciones-y-umbral

## Status
15/15 tasks complete. Ready for verification.

## Completed Tasks
- [x] 1.1 Create `backend/app/models/calificacion.py` with `Calificacion` model inheriting from `TimestampedTenant`.
- [x] 1.2 Create `backend/app/models/umbral.py` with `UmbralMateria` model inheriting from `TimestampedTenant`.
- [x] 1.3 Add models to `backend/app/models/__init__.py`.
- [x] 1.4 Generate Alembic migration for `Calificacion` and `UmbralMateria`.
- [x] 2.1 Create `backend/app/schemas/calificacion.py` (Preview, Import, Response).
- [x] 2.2 Create `backend/app/schemas/umbral.py` (Config, Response).
- [x] 2.3 Create `backend/app/repositories/calificacion.py` implementing bulk insert and isolated delete filtered by `actor_id` and `materia_id`.
- [x] 2.4 Create `backend/app/repositories/umbral.py` for configuring default thresholds.
- [x] 2.5 Create `backend/app/services/calificacion_service.py` to parse CSV, map `EntradaPadron.email_hash`, and evaluate approval status based on `UmbralMateria`.
- [x] 3.1 Create `backend/app/api/v1/routers/calificaciones.py` with endpoints for preview, import, and clearing grades.
- [x] 3.2 Add `UmbralMateria` management endpoints to `calificaciones.py` or separate router.
- [x] 3.3 Register the new router in `backend/app/main.py` under the `/api/v1/calificaciones` prefix.
- [x] 4.1 Write unit tests for `calificacion_service.py` (numerical vs textual threshold evaluation).
- [x] 4.2 Write integration tests for `calificacion_repository.py` to ensure isolated deletion by `actor_id`.
- [x] 4.3 Write E2E tests for the CSV preview and import endpoints.

## Files Changed
| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/models/calificacion.py` | Created | Defined the Calificacion model with relationships and indices. |
| `backend/app/models/umbral.py` | Created | Defined the UmbralMateria model. |
| `backend/app/models/__init__.py` | Modified | Exported new models. |
| `backend/alembic/versions/fbbfb2cc45f9_create_calificacion_and_umbral.py` | Created | Alembic migration file. |
| `backend/app/schemas/calificacion.py` | Created | Defined Pydantic schemas for preview, import, response of grades. |
| `backend/app/schemas/umbral.py` | Created | Defined Pydantic schemas for UmbralMateria config. |
| `backend/app/repositories/calificacion.py` | Created | DB layer for Calificacion (isolated clear, bulk upsert, queries). |
| `backend/app/repositories/umbral.py` | Created | DB layer for UmbralMateria configuration. |
| `backend/app/services/calificacion_service.py` | Created | Services logic for previewing/importing CSV and checking thresholds. |
| `backend/app/api/v1/routers/calificaciones.py` | Created | Endpoints for preview, import, clear, and thresholds. |
| `backend/app/main.py` | Modified | Registered qualifications router. |
| `backend/tests/test_calificacion_service.py` | Created | Unit/Service tests for grading logic. |
| `backend/tests/test_calificacion_repository.py` | Created | Integration tests for repository operations. |
| `backend/tests/api/test_calificaciones_api.py` | Created | End-to-end tests for all router endpoints. |

## Workload / PR Boundary
- Mode: chained PR slice
- Current work unit: API & Tests (PR 3)
- Boundary: Tasks 3.1 to 4.3
- Estimated review budget impact: ~250 lines (cumulative ~750 lines)
