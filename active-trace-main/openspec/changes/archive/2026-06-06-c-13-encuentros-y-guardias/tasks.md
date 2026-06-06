# Tasks: C-13 Encuentros y Guardias

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~500 lines |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Encuentros) → PR 2 (Guardias) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Dominio Encuentros | PR 1 | Modelos, Schemas, Repos, Service, Router, Tests de Slot e Instancia. Incluye migración DB combinada. |
| 2 | Dominio Guardias | PR 2 | Modelos, Schemas, Repos, Service, Router, Tests de Guardia. Depende de PR 1 para mantener tests pasantes. |

## Phase 1: Modelos y Migración de Base de Datos

- [x] 1.1 Crear `backend/app/models/encuentro.py` con `SlotEncuentro` e `InstanciaEncuentro`.
- [x] 1.2 Crear `backend/app/models/guardia.py` con `Guardia`.
- [x] 1.3 Ejecutar autogeneración de migración Alembic en `backend/alembic/versions/`.

## Phase 2: Schemas y Repositorios

- [x] 2.1 Crear `backend/app/schemas/encuentro.py` (DTOs entrada/salida).
- [x] 2.2 Crear `backend/app/schemas/guardia.py` (DTOs entrada/salida).
- [x] 2.3 Crear `backend/app/repositories/encuentro_repository.py` con query scopes.
- [x] 2.4 Crear `backend/app/repositories/guardia_repository.py` con query scopes.

## Phase 3: Lógica de Negocio (Services)

- [x] 3.1 Crear `backend/app/services/encuentro_service.py` con la función iterativa `generar_instancias`.
- [x] 3.2 Crear `backend/app/services/guardia_service.py` para lógica de turnos.

## Phase 4: API y Routing

- [x] 4.1 Crear `backend/app/api/v1/routers/encuentros.py` asegurado con `require_permission("encuentros:gestionar")`.
- [x] 4.2 Crear `backend/app/api/v1/routers/guardias.py` asegurado.
- [x] 4.3 Modificar `backend/app/main.py` agregando los `include_router`.

## Phase 5: Testing

- [x] 5.1 Crear `backend/tests/api/test_encuentros.py` (verificando fechas bisiestas y saltos de mes en service).
- [x] 5.2 Crear `backend/tests/api/test_guardias.py` (verificando endpoint creation & list).
