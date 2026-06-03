# Tasks: c-10-calificaciones-y-umbral

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 600 - 800 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Models) → PR 2 (Repos/Services) → PR 3 (API/Tests) |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Database Foundation | PR 1 | Models and Alembic migration. |
| 2 | Core Logic | PR 2 | Repositories, Schemas, and Service logic. Base: PR 1 branch. |
| 3 | API & Tests | PR 3 | FastApi router, app wiring, and end-to-end tests. Base: PR 2 branch. |

## Phase 1: Foundation (Models & DB)

- [x] 1.1 Create `backend/app/models/calificacion.py` with `Calificacion` model inheriting from `TimestampedTenant`.
- [x] 1.2 Create `backend/app/models/umbral.py` with `UmbralMateria` model inheriting from `TimestampedTenant`.
- [x] 1.3 Add models to `backend/app/models/__init__.py`.
- [x] 1.4 Generate Alembic migration for `Calificacion` and `UmbralMateria`.

## Phase 2: Core Implementation (Repositories, Schemas & Services)

- [x] 2.1 Create `backend/app/schemas/calificacion.py` (Preview, Import, Response).
- [x] 2.2 Create `backend/app/schemas/umbral.py` (Config, Response).
- [x] 2.3 Create `backend/app/repositories/calificacion.py` implementing bulk insert and isolated delete filtered by `actor_id` and `materia_id`.
- [x] 2.4 Create `backend/app/repositories/umbral.py` for configuring default thresholds.
- [x] 2.5 Create `backend/app/services/calificacion_service.py` to parse CSV, map `EntradaPadron.email_hash`, and evaluate approval status based on `UmbralMateria`.

## Phase 3: Integration (API Routers)

- [x] 3.1 Create `backend/app/api/v1/routers/calificaciones.py` with endpoints for preview, import, and clearing grades.
- [x] 3.2 Add `UmbralMateria` management endpoints to `calificaciones.py` or separate router.
- [x] 3.3 Register the new router in `backend/app/main.py` under the `/api/v1/calificaciones` prefix.

## Phase 4: Testing & Verification

- [x] 4.1 Write unit tests for `calificacion_service.py` (numerical vs textual threshold evaluation).
- [x] 4.2 Write integration tests for `calificacion_repository.py` to ensure isolated deletion by `actor_id`.
- [x] 4.3 Write E2E tests for the CSV preview and import endpoints.
