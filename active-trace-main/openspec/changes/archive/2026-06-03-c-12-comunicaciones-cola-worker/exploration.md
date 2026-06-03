## Exploration: C-12 comunicaciones-cola-worker

### Current State

El sistema cuenta con C-01 a C-11 implementados: infraestructura, tenancy, auth, RBAC, audit, estructura académica, usuarios, equipos, padrón, calificaciones y análisis de atrasados. C-11 provee `AnalisisService` con `alumnos_atrasados`, cada uno con email descifrado de `EntradaPadron.email` — fuente directa de destinatarios para C-12.

El worker (`backend/app/workers/main.py`) existe pero es un placeholder: `asyncio.sleep(3600)`. No hay modelo `Comunicacion`, ni lógica de cola, ni integración SMTP.

**Infraestructura reutilizable disponible:**
- `core/security.py` — `encrypt_attr()` / `decrypt_attr()` + `generate_email_hash()`
- `core/types.py` — `EncryptedString` TypeDecorator (ya en uso en `EntradaPadron.email`, `Usuario.email/dni/cbu`)
- `services/audit.py` — `AuditService.log_action()` + `AuditLog` append-only
- `repositories/base.py` — `BaseRepository[T]` con tenant scope automático y soft delete
- `core/dependencies.py` — `require_permission("modulo:accion")` guard (retorna `CurrentUser`)
- Migración head: `fbbfb2cc45f9` (C-10)

**Gap crítico:** `app/core/exceptions.py` es un docstring placeholder vacío — `ServiceError` no existe y debe crearse.

### Affected Areas

- `backend/app/models/comunicacion.py` (NUEVO) — Modelo `Comunicacion` (E21) con `EncryptedString` para `destinatario`
- `backend/app/models/tenant.py` (MODIFICAR) — Agregar `aprobacion_comunicaciones_masivas: Boolean`
- `backend/app/repositories/comunicacion.py` (NUEVO) — Extiende `BaseRepository[Comunicacion]`
- `backend/app/services/comunicacion_service.py` (NUEVO) — Encolar, preview, aprobar, cancelar, máquina de estados
- `backend/app/workers/main.py` (REEMPLAZAR) — Worker real: crash recovery + poll loop + dispatch
- `backend/app/api/v1/routers/comunicaciones.py` (NUEVO) — 8 endpoints
- `backend/app/main.py` (MODIFICAR) — Registrar router
- `backend/app/schemas/comunicacion.py` (NUEVO) — DTOs Pydantic v2
- `backend/app/core/config.py` (MODIFICAR) — SMTP + worker settings
- `backend/app/core/exceptions.py` (MODIFICAR) — Crear `ServiceError`
- `backend/alembic/versions/XXXX_c12_comunicacion.py` (NUEVO) — `down_revision='fbbfb2cc45f9'`
- `backend/pyproject.toml` (MODIFICAR) — Agregar `aiosmtplib>=3.0.0`

### Approaches

1. **asyncio loop con poll DB** — Worker hace polling sobre la tabla `comunicacion` buscando filas `PENDIENTE AND aprobado=True`. Sin infraestructura nueva.
   - Pros: Cero deps nuevas (aparte de aiosmtplib), testeable contra DB real, interfaz de repo estable si se migra a broker después.
   - Cons: Polling overhead, single-process assumption, doble-send window en crash.
   - Effort: Medium

2. **ARQ + Redis** — Queue broker con workers escalables y retry automático.
   - Pros: Alta throughput, auto-retry, sin polling.
   - Cons: Redis no está en el stack, ADR-003 abierto, testing más complejo.
   - Effort: High

3. **Delegar a N8N** — N8N ya está en el stack de integración.
   - Pros: N8N ya en stack.
   - Cons: Acoplamiento externo, sincronización de estado compleja, debugging opaco.
   - Effort: High

### Recommendation

**asyncio loop con poll DB** (Opción 1). ADR-003 está explícitamente abierto. Sin decisión cerrada, el enfoque mínimo evita nueva infraestructura. La recuperación de crash es trivial (ENVIANDO → PENDIENTE al arrancar). La máquina de estados vive íntegramente en Python, testeable contra DB real per reglas del proyecto. Si ARQ o N8N se adoptan después, solo cambia `workers/main.py` — modelo, servicio y repo son invariantes.

### Risks

- **ADR-003 abierto**: asyncio loop es provisional. Documentar como provisional en `docs/ARQUITECTURA.md`.
- **Double-send en crash**: si el worker muere entre SMTP-sent y DB-commit, el mensaje se reintenta al reiniciar. Mitigación: commit inmediato post-SMTP. Riesgo aceptado.
- **SMTP en tests**: mockear `aiosmtplib.send` es legítimo (transporte externo, no DB). DB mocking sigue prohibido.
- **`ServiceError` ausente**: debe crearse en `core/exceptions.py` antes de implementar el service.
- **Patrón de router incorrecto**: `require_permission()` retorna `CurrentUser` — patrón de un solo `Depends`, no dos. Ver `api/v1/routers/analisis.py`.
- **FK plural**: `materia_id → materias.id` (tabla plural), no `materia.id`.

### Ready for Proposal

Yes — C-11 implementado provee la fuente de destinatarios. Toda la infraestructura de patrones (cifrado, audit, repositorio, RBAC) es directamente reutilizable. Las decisiones de diseño están cerradas por el usuario.
