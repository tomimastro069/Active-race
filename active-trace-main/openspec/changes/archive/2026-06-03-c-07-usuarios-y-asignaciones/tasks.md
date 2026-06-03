# Tasks: C-07 Usuarios y Asignaciones

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 750-850 lines |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Data Layer) → PR 2 (Logic) → PR 3 (API) |
| Delivery strategy | exception-ok |
| Chain strategy | exception-ok |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: exception-ok
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Data Layer & Crypto | PR 1 | Base branch: `main`. Includes TypeDecorator, Models, and Alembic migration. |
| 2 | Schemas, Repos, Services | PR 2 | Base branch: `PR 1`. Includes business logic and repository updates. |
| 3 | API Routers & E2E Tests | PR 3 | Base branch: `PR 2`. Exposes endpoints and completes E2E tests. |

## Phase 1: Foundation (Data Layer & Crypto)

- [x] 1.1 Create `backend/app/core/types.py` with `EncryptedString` SQLAlchemy TypeDecorator using `app.core.security`.
- [x] 1.2 Modify `backend/app/models/usuario.py` to add `email_hash` and PII fields (`dni`, `cuil`, etc.) using `EncryptedString`.
- [x] 1.3 Modify `backend/app/models/asignacion.py` to add `estado_vigencia` property.
- [x] 1.4 Generate Alembic migration in `backend/alembic/versions/` (schema additions and data migration for existing users).
- [x] 1.5 Write unit tests for `EncryptedString` and `estado_vigencia`.

## Phase 2: Core Implementation (Repositories & Services)

- [x] 2.1 Create `backend/app/schemas/usuario.py` and `backend/app/schemas/asignacion.py` with Pydantic models.
- [x] 2.2 Modify `backend/app/repositories/usuario.py` to support exact lookup by `email_hash`.
- [x] 2.3 Create `backend/app/repositories/asignacion.py` to handle CRUD of assignments.
- [x] 2.4 Create `backend/app/services/usuario.py` to handle `email_hash` generation and PII masking.
- [x] 2.5 Create `backend/app/services/asignacion.py` for business logic and validation of dates.
- [x] 2.6 Write integration tests for `UsuarioRepository` (verifying `email_hash` uniqueness).

## Phase 3: Integration (API Routers)

- [x] 3.1 Create `backend/app/api/v1/routers/usuarios.py` with `/api/admin/usuarios` endpoints, guarded by `usuarios:gestionar`.
- [x] 3.2 Create `backend/app/api/v1/routers/asignaciones.py` with `/api/asignaciones` endpoints, guarded by `equipos:asignar`.
- [x] 3.3 Register new routers in `backend/app/api/v1/routers/__init__.py` or main app file.

## Phase 4: Testing & Cleanup

- [x] 4.1 Write E2E tests for `/api/admin/usuarios` endpoints (verifying PII masking).
- [x] 4.2 Write E2E tests for `/api/asignaciones` endpoints (verifying guards).
- [x] 4.3 Clean up any unused imports and run linter on new files.

