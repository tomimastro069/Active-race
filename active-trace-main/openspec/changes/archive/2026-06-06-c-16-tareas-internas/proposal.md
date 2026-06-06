# Proposal: Tareas Internas (c-16-tareas-internas)

## Intent
Implement a backend tracking and communication system for academic/internal tasks between coordinators, teachers, and tutors. This addresses the need for structured internal coordination (Epic 8) and resolves asynchronous tracking for high volumes of tasks (hundreds active simultaneously).

## Scope

### In Scope
- Models `Tarea` (id, tenant_id, materia_id, asignado_a, asignado_por, estado, descripcion, contexto_id) and `ComentarioTarea` (id, tenant_id, tarea_id, autor_id, texto).
- API endpoints `/api/v1/tareas/*` with permissions `tareas:gestionar` (filters, global admin, delegate) and `tareas:gestionar_propio` (view own, change status, add comment).
- DB migration for the new models.
- Tests (creation, assignment, delegation, state changes, comments, filters).

### Out of Scope
- Frontend UI views (shell / components). This proposal only targets backend APIs.
- Real-time notification socket push (we use async comments/status polling).

## Capabilities

### New Capabilities
- `tareas-internas`: Internal task tracking, states, delegation, and nested comment threads for coordination.

### Modified Capabilities
None

## Approach
- Implement `Tarea` and `ComentarioTarea` models using SQLAlchemy 2.0 async. Inherit from `Base` and `TimestampedTenant`.
- Create `TareaRepository` and `ComentarioRepository` inheriting from `BaseRepository` to leverage automatic tenant-level query scoping.
- Implement `TareaService` to manage status transitions, delegation traceability, and thread comments.
- Add FastAPI routes under `/api/v1/tareas` secured with `require_permission`.
- Write unit/integration tests ensuring proper tenant isolation, RBAC validation (mocking the `Authorization` header to avoid TenantMiddleware 401s), and status transitions.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/` | New | Create `tarea.py` (Tarea, ComentarioTarea) |
| `backend/app/models/__init__.py` | Modified | Export Tarea models |
| `backend/app/repositories/` | New | Create `tarea_repository.py` and `comentario_repository.py` |
| `backend/app/repositories/__init__.py` | Modified | Export Tarea repositories |
| `backend/app/schemas/` | New | Create `tarea.py` DTOs |
| `backend/app/services/` | New | Create `tarea_service.py` |
| `backend/app/api/v1/routers/` | New | Create `tareas.py` router |
| `backend/app/main.py` | Modified | Mount `tareas.py` router under `/api/v1` |
| `backend/alembic/versions/` | New | DB migration |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Missing `Authorization` header in API tests causes 401 | High | Include mock auth headers in all `AsyncClient` test calls |
| N+1 query loading comments/relationships | Med | Use `selectinload` for comments and user relations |

## Rollback Plan
Run alembic downgrade to revert database migration, delete created files, and revert modifications in `main.py` and model exports.

## Dependencies
- C-07 (Usuarios y Asignaciones)

## Success Criteria
- [ ] DB migration applies and rollbacks cleanly.
- [ ] Endpoints `/api/v1/tareas` enforce tenant isolation.
- [ ] Users can retrieve tasks, post comments, and change states if authorized.
- [ ] API integration tests achieve >=80% code coverage.
