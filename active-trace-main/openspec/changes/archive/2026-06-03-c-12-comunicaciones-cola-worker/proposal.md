# Proposal: C-12 — comunicaciones-cola-worker

## What & Why

C-12 implements the outbound communications module: a `Comunicacion` model, an asynchronous dispatch worker, mandatory preview, batch sending with a queue, and per-tenant human approval. It is the **FINAL change of the critical path** (`C-01 → C-02 → C-03 → C-04 → C-06 → C-07 → C-09 → C-10 → C-11 → C-12`).

Why it closes the critical path: the highest-value product flow is "import → analyze → communicate". C-09/C-10 import grades, C-11 computes late students (atrasados) and rankings. C-12 is what lets a PROFESOR act on that analysis by reaching out to at-risk students. Without it, the product can observe but never intervene. After C-12, the full backend value loop runs in multi-tenant production.

It is also the first change to give the placeholder worker (`backend/app/workers/main.py`, currently a no-op `asyncio.sleep(3600)`) a real job, establishing the queue/state-machine pattern that future async modules can reuse.

## Scope

### In scope
- **Model `Comunicacion` (E21)**: `id`, `tenant_id`, `enviado_por` (FK Usuario), `materia_id` (FK Materia), `destinatario` (EncryptedString, AES-256), `destinatario_hash` (deterministic, added from the start), `asunto`, `cuerpo`, `estado` (enum Pendiente|Enviando|Enviado|Error|Cancelado), `lote_id` (UUID nullable), `enviado_at` (nullable), `intentos` (int, for bounded retry), plus mixin fields (`created_at`, `updated_at`, `deleted_at` soft delete).
- **State machine (RN-15)**: explicit valid/invalid transitions. Pendiente → Enviando → Enviado | Error; Pendiente → Cancelado. Invalid transitions rejected at service level.
- **Mandatory preview (F3.1, RN-16)**: `POST /api/comunicaciones/preview` renders subject + body with variable substitution; no dispatch without explicit confirmation.
- **Batch sending with queue (F3.2)**: a single send to N recipients shares one `lote_id`; rows enqueued as Pendiente.
- **Per-tenant human approval (F3.3, RN-17)**: explicit `Boolean` column `aprobacion_comunicaciones_masivas` on `tenant`. When the flag is active, ANY batch (any row with `lote_id` present) requires approval. Guard `comunicacion:aprobar`. Approval/cancel works at batch (`lote_id`) OR individual level.
- **Async worker (`workers/main.py`)**: asyncio loop polling the DB. Crash recovery on startup (Enviando → Pendiente). Picks Pendiente rows that are approved-or-not-requiring-approval, transitions through the state machine, dispatches via SMTP, writes `COMUNICACION_ENVIAR` audit on success.
- **Bounded automatic retry**: simple `intentos` counter; on dispatch failure, increment and re-queue up to `MAX_INTENTOS` (configurable, default 3), then settle to Error.
- **Endpoints `/api/comunicaciones/*`**: preview, enqueue (`comunicacion:enviar`), list/status, approve/cancel by batch or individual (`comunicacion:aprobar`).
- **Audit**: `COMUNICACION_ENVIAR` per successful dispatch.
- **Migration**: `down_revision = 'fbbfb2cc45f9'` (latest existing). Creates table `comunicacion` + 4 indexes + Boolean column on `tenant`.
- **Config**: SMTP settings + worker tuning in `core/config.py`.
- **Schemas**: DTOs with `extra='forbid'` in `schemas/comunicacion.py`.
- **Tests (Strict TDD, real/ephemeral DB)**: state machine, preview, approval, cancellation, encrypted destinatario round-trip, worker lifecycle, crash recovery, bounded retry.

### Out of scope
- No Redis/ARQ/N8N broker (ADR-003 stays provisional).
- No frontend (C-22 `frontend-academico-docente`).
- No inbound mailbox / internal messaging (C-20).
- No bounce-handling, webhooks, or delivery receipts beyond SMTP success/failure.
- No reusable tenant config framework (JSONB) — only the single explicit approval Boolean.

## Design Decisions (6 closed)

1. **Worker engine: asyncio loop polling the DB.** No Redis, no ARQ, no N8N. Zero new infrastructure, testable against real DB, stable repo interface if broker adopted later. ADR-003 recorded as provisional.

2. **Tenant approval flag: explicit `Boolean` column `aprobacion_comunicaciones_masivas` on `tenant`.** Type-safe, readable in code review, trivially queryable. YAGNI on a generic config bag.

3. **Mass threshold: ANY batch requires approval when flag is active.** A row is "batch" when `lote_id` is present. No N-recipient threshold. Simplest correct rule, fail-closed for ALTO governance.

4. **Template engine: `string.Template` (stdlib).** No new dependency, safe `$var` substitution, sufficient for subject/body variable substitution.

5. **Automatic retry: bounded counter (`intentos`).** On dispatch failure, increment `intentos` and re-queue up to `MAX_INTENTOS`, then settle to Error. Simple, no backoff scheduler, no external queue.

6. **`destinatario_hash` from the start.** Deterministic hash alongside encrypted `destinatario`, mirroring existing `email_hash` pattern in `EntradaPadron`/`Usuario`.

## Dependencies

- **C-11 `analisis-atrasados-reportes`** (completed): recipient email source is `EntradaPadron.email` (AES-256 encrypted).
- **Reusable infrastructure**: `EncryptedString` TypeDecorator, `generate_email_hash()`, `BaseRepository[T]`, `AuditService.log_action()`, `require_permission()` guard.
- **Migration chain**: builds on `fbbfb2cc45f9` (C-10 calificacion/umbral).

## Residual Risks

1. **Double-send**: crash after SMTP success but before `ENVIANDO→ENVIADO` commit re-dispatches on recovery. Mitigation: commit immediately post-SMTP. Accepted risk for C-12.
2. **ADR-003 provisional**: asyncio-loop-vs-broker. Repo interface is the stable boundary — worker dispatch loop can be swapped without touching service or model contracts.
3. **SMTP external transport**: tests mock the transport (legitimate — external transport, NOT DB mocking which remains forbidden).
4. **Governance ALTO**: checkpoints required; encrypted-recipient handling, approval gate, and audit wiring need human review before merge.

## Affected Files

| File | Action |
|------|--------|
| `backend/app/models/comunicacion.py` | CREATE |
| `backend/app/models/tenant.py` | MODIFY (add `aprobacion_comunicaciones_masivas`) |
| `backend/app/repositories/comunicacion.py` | CREATE |
| `backend/app/services/comunicacion_service.py` | CREATE |
| `backend/app/workers/main.py` | REPLACE placeholder |
| `backend/app/api/v1/routers/comunicaciones.py` | CREATE |
| `backend/app/main.py` | MODIFY (register router) |
| `backend/app/schemas/comunicacion.py` | CREATE |
| `backend/app/core/config.py` | MODIFY (SMTP + worker settings) |
| `backend/app/core/exceptions.py` | MODIFY (create ServiceError) |
| `backend/alembic/versions/XXXX_c12_comunicacion.py` | CREATE (`down_revision='fbbfb2cc45f9'`) |
| `backend/tests/test_comunicacion_service.py` | CREATE |
| `backend/tests/test_comunicacion_worker.py` | CREATE |
