# Tasks: C-12 — comunicaciones-cola-worker

> Delivery: 3 PRs stacked-to-main
> PR-1 (T-01→T-08): prerequisites + model + migration (~172 LOC)
> PR-2 (T-09→T-15): repository + schemas + service + TDD (~490 LOC)
> PR-3 (T-16→T-19): router + worker + verification (~312 LOC)

---

## PR-1: Foundation + Model + Migration

### Grupo 0 — Prerequisites (no tests)

- [x] **T-01**: Add `aiosmtplib` dependency (`backend/pyproject.toml`)
  - Agrega `"aiosmtplib>=3.0.0"` a `[project].dependencies`. Verificado ausente del archivo actual.

- [x] **T-02**: Add SMTP + worker config (`backend/app/core/config.py`)
  - Agrega 7 campos a `Settings`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `WORKER_POLL_INTERVAL_SECONDS: int = 30`, `MAX_INTENTOS: int = 3`.

- [x] **T-03**: Create `ServiceError` (`backend/app/core/exceptions.py`)
  - Define `class ServiceError(Exception)`. Archivo es un docstring placeholder vacío hoy — confirmado.
  - Routers mapean `ServiceError` → 422 por defecto, → 409 en cancelación individual.

### Grupo 1 — Model + Migration

- [x] **T-04+T-05**: Create `Comunicacion` model (`backend/app/models/comunicacion.py`)
  - Define `EstadoComunicacion(str, enum.Enum)` (5 valores: Pendiente/Enviando/Enviado/Error/Cancelado).
  - Define `class Comunicacion(Base, TimestampedTenant)` con todos los campos del spec §1 y 4 indexes.
  - FK: `ForeignKey("usuario.id")` y `ForeignKey("materias.id")` (tabla **plural** — crítico).
  - `tenant_id` lo provee el mixin; NO agregar FK explícita sobre él.
  - `__repr__` NUNCA incluye `destinatario`.

- [x] **T-06**: Register `Comunicacion` in `backend/app/models/__init__.py`
  - Agrega `from app.models.comunicacion import Comunicacion, EstadoComunicacion` + añadir a `__all__`.
  - CRÍTICO: sin este import, `Base.metadata.create_all` en conftest no crea la tabla.

- [x] **T-07**: Add `aprobacion_comunicaciones_masivas` to `Tenant` (`backend/app/models/tenant.py`)
  - `Column(Boolean, nullable=False, default=False, server_default="false")`.

- [x] **T-08**: Create Alembic migration (`backend/alembic/versions/bc500c50d1fd_c12_comunicacion.py`)
  - `down_revision = 'fbbfb2cc45f9'` (head actual confirmado).
  - Upgrade: (1) add_column tenant; (2) crear enum `estadocomunicacion` con `checkfirst=True`; (3) create_table 'comunicacion'; (4) create_index x4.
  - Downgrade: drop indexes → drop table → `DROP TYPE IF EXISTS estadocomunicacion` → drop column.

---

## PR-2: Repository + Schemas + Service (TDD)

### Grupo 2 — Repository

- [x] **T-09**: TDD `ComunicacionRepository` (`backend/app/repositories/comunicacion.py` + `backend/tests/test_comunicacion_repository.py`)
  - TDD: SC-ENC-01 Case B, SC-ENQ-01/02, SC-APR-01/02, SC-CAN-01.
  - Constructor: `__init__(self, session, tenant_id)` → `super().__init__(Comunicacion, session, tenant_id)`.
  - Métodos adicionales:
    - `list_by_lote(lote_id)` — tenant-scoped
    - `list_by_estado_sistema(estado)` — cross-tenant, NO `_apply_tenant_scope`, doc comment obligatorio
    - `list_dispatchable()` — cross-tenant, PENDIENTE AND aprobado=True AND deleted_at IS NULL, doc comment obligatorio
    - `list_filtered(estado, lote_id, enviado_por, skip, limit)` — tenant-scoped, paginado
    - `lote_resumen(lote_id)` — GROUP BY estado, tenant-scoped
    - `bulk_approve_lote(lote_id)` — flip aprobado=True solo en PENDIENTE, flush(), retorna count
    - `bulk_cancel_lote(lote_id)` — CANCELADO solo en PENDIENTE, flush(), retorna count

### Grupo 3 — Schemas

- [x] **T-10**: Create Pydantic DTOs (`backend/app/schemas/comunicacion.py`)
  - Todos `ConfigDict(extra='forbid')`. 6 schemas:
    1. `DestinatarioItem(email, nombre, actividades_faltantes="")`
    2. `ComunicacionPreviewRequest(asunto_template, cuerpo_template, variables: dict[str,str])`
    3. `ComunicacionPreviewResponse(asunto_renderizado, cuerpo_renderizado)`
    4. `ComunicacionEnviarRequest(asunto_template, cuerpo_template, destinatarios: list[DestinatarioItem] min_length=1, materia_id: UUID)`
    5. `ComunicacionResponse` — **NUNCA incluir campo `destinatario`**. Usar `ConfigDict(from_attributes=True, extra='forbid')`.
    6. `LoteResumenResponse(lote_id, total, por_estado: dict[str,int])`
  - TDD: SC-ENC-01 Case A — test `"destinatario" not in ComunicacionResponse.model_fields`.

### Grupo 4 — Service

- [x] **T-11**: TDD state machine + pure helpers (`test_comunicacion_service.py` + inicio de `comunicacion_service.py`)
  - TDD: SC-SM-01, SC-SM-02, SC-SM-03, SC-PRV-01, SC-PRV-02, SC-PRV-03.
  - Implementar: `VALID_TRANSITIONS` dict, `_assert_transition(current, target)`, `_render(template_str, variables)` via `string.Template.safe_substitute`.
  - Tests 100% sincrónicos/unitarios (sin DB).

- [x] **T-12**: TDD preview (`test_comunicacion_service.py` + `ComunicacionService.preview`)
  - TDD: SC-PRV-04.
  - `class ComunicacionService(__init__(self, db, tenant_id))`. Método `preview()` síncrono, sin DB.

- [x] **T-13**: TDD encolar (`test_comunicacion_service.py` + `ComunicacionService.encolar`)
  - TDD: SC-ENQ-01, SC-ENQ-02, SC-ENQ-03.
  - `enviado_por = current_user.id` (JWT, NUNCA body). `tenant_id = current_user.tenant_id`.

- [x] **T-14**: TDD aprobación (`test_comunicacion_service.py` + `aprobar_lote`, `aprobar_individual`)
  - TDD: SC-APR-01, SC-APR-02.
  - `aprobar_individual` es idempotente: si ENVIADO → no-op, retorna row (HTTP 200).

- [x] **T-15**: TDD cancelación (`test_comunicacion_service.py` + `cancelar_lote`, `cancelar_individual`)
  - TDD: SC-CAN-01, SC-CAN-02.
  - `cancelar_individual`: `_assert_transition(row.estado, CANCELADO)` lanza ServiceError en ENVIADO/CANCELADO/ENVIANDO.

---

## PR-3: Router + Worker + Verification

### Grupo 5 — Router

- [x] **T-16**: Create router (`backend/app/api/v1/routers/comunicaciones.py`)
  - 8 handlers. Patrón REAL: `current_user: CurrentUser = Depends(require_permission("comunicacion:enviar"))`.
  - NO usar `get_current_user` + `require_permission` separados — ese patrón es incorrecto en este repo.
  - Endpoints: preview (200), enqueue (201), list (200), lote-summary (200), approve-lote, approve-individual, cancel-lote, cancel-individual.
  - Cancel individual: catch `ServiceError` → HTTP 409.

- [x] **T-17**: Register router in `backend/app/main.py`
  - `app.include_router(comunicaciones_router, prefix="/api/v1")`.
  - Registro en `main.py`, NO en `routers/__init__.py` (está vacío — confirmado).

### Grupo 6 — Worker

- [x] **T-18**: TDD worker (`backend/tests/test_comunicacion_worker.py` + `backend/app/workers/main.py` REPLACE)
  - TDD: SC-WRK-01, SC-WRK-02, SC-WRK-03, SC-WRK-04, SC-WRK-05, SC-AUD-01.
  - Mock: `unittest.mock.AsyncMock` patchando `app.workers.main.aiosmtplib.send`.
  - Funciones testables (no `while True`):
    - `recover_stuck(session) -> int` — crash recovery
    - `poll_once(session, settings) -> None` — un ciclo de poll
    - `dispatch_one(row, session, settings) -> None` — máquina de estados + SMTP + audit
    - `run_worker() -> None` — entrypoint real con loop
  - SEGURIDAD: `dispatch_one` NUNCA loguea `row.destinatario`. Logger usa `row.id`, `row.destinatario_hash`, `row.estado.value`.

### Grupo 7 — Verification

- [x] **T-19**: Full test suite + coverage
  - `cd backend && python3 -m pytest tests/test_comunicacion_service.py tests/test_comunicacion_worker.py tests/test_comunicacion_repository.py -v --tb=short`
  - Confirmar ≥80% líneas, ≥90% reglas de negocio (state machine, approval gating, retry logic).

---

## Review Workload Forecast

| Componente | LOC prod (est.) | LOC tests (est.) |
|---|---|---|
| T-01→T-03 (prerequisites) | ~12 | — |
| T-04+T-05 (model) | ~70 | — |
| T-06→T-08 (registration + migration) | ~90 | — |
| T-09 (repository) | ~90 | ~60 |
| T-10 (schemas) | ~70 | — |
| T-11→T-15 (service) | ~120 | ~150 |
| T-16→T-17 (router) | ~92 | — |
| T-18 (worker) | ~100 | ~120 |
| **TOTAL** | **~644** | **~330** |
| **Combinado** | **~974 LOC** | |
