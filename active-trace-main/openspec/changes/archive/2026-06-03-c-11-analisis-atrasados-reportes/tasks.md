# Tasks: C-11 analisis-atrasados-reportes

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 600 - 750 lines |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Service/DB) → PR 2 (API/Schemas) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Service layer & Repositories | PR 1 | Base branch: `main`. Includes `AnalisisService` and DB queries, with unit tests. |
| 2 | API Routers & Schemas | PR 2 | Base branch: `feature/c-11-tracker` (or PR 1). Exposes the service logic via HTTP endpoints with integration tests. |

## Phase 1: Foundation (Data Layer)
- [x] 1.1 `backend/app/repositories/calificacion.py`: Add `get_distinct_activities` grouping.
- [x] 1.2 `backend/app/repositories/calificacion.py`: Add `get_ungraded_textual_calificaciones` filter.
- [x] 1.3 `backend/app/repositories/padron_repository.py`: Add specific lookup helpers if missing.

## Phase 2: Core Implementation (Service Layer - PR 1)
- [x] 2.1 `backend/app/services/analisis_service.py`: Implement `obtener_alumnos_atrasados` (RN-06).
- [x] 2.2 `backend/app/services/analisis_service.py`: Implement `obtener_ranking_aprobados` (RN-09).
- [x] 2.3 `backend/app/services/analisis_service.py`: Implement `obtener_notas_finales` and `obtener_reporte_rapido`.
- [x] 2.4 `backend/app/services/analisis_service.py`: Implement `obtener_tps_sin_corregir` and monitor multi-filter.

## Phase 3: Unit Testing (PR 1)
- [x] 3.1 `backend/tests/test_analisis_service.py`: Write strict TDD test asserting delayed logic (qualitative & quantitative).
- [x] 3.2 `backend/tests/test_analisis_service.py`: Assert ranking excludes students with 0 approvals.

## Phase 4: API & Integration (PR 2)
- [x] 4.1 `backend/app/schemas/analisis.py`: Define `AlumnoAtrasadoResponse`, `RankingResponse`, etc.
- [x] 4.2 `backend/app/api/v1/routers/analisis.py`: Implement `/api/v1/analisis/` with GET endpoints and RBAC guards.
- [x] 4.3 `backend/app/main.py`: Include `analisis_router`.

## Phase 5: API Testing (PR 2)
- [x] 5.1 `backend/tests/api/test_analisis_api.py`: Test endpoint auth (`atrasados:ver_propio`).
- [x] 5.2 `backend/tests/api/test_analisis_api.py`: Validate correct schema return structures.


