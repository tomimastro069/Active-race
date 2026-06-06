# Tasks: Tareas Internas

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250-350 lines |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full implementation of Tareas Internas backend and tests | PR 1 | Base branch; tests and migration included. |

## Phase 1: Database and Models

- [x] 1.1 Create models in `backend/app/models/tarea.py` (implementing `EstadoTareaEnum`, `Tarea`, `ComentarioTarea`).
- [x] 1.2 Export models in `backend/app/models/__init__.py`.
- [x] 1.3 Create Alembic migration for `tareas` and `comentarios_tarea` tables.

## Phase 2: Repositories and Schemas

- [x] 2.1 Create Pydantic schemas in `backend/app/schemas/tarea.py` for task creation, status updates, and comments.
- [x] 2.2 Create `TareaRepository` and `ComentarioTareaRepository` in `backend/app/repositories/tarea_repository.py`.
- [x] 2.3 Export repositories in `backend/app/repositories/__init__.py`.

## Phase 3: Service and Router

- [x] 3.1 Create `TareaService` in `backend/app/services/tarea_service.py` to handle creation, transitions, and comments.
- [x] 3.2 Create API endpoints in `backend/app/api/v1/routers/tareas.py`.
- [x] 3.3 Register the new router in `backend/app/main.py`.

## Phase 4: Verification and Tests

- [x] 4.1 Write integration tests in `backend/tests/api/test_tareas_api.py` covering: creation, delegation, states, and isolation.
- [x] 4.2 Run and verify test suite with `pytest`.
