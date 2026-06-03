# comunicaciones-cola-worker Specification

## Purpose

Define el módulo de comunicaciones salientes con cola y worker asíncrono. Permite a un PROFESOR enviar mensajes a alumnos atrasados con preview obligatorio, aprobación humana configurable por tenant, envío masivo con lote, máquina de estados auditable y reintento acotado. Cierra el camino crítico del sistema: importar → analizar → comunicar.

## Requirements

### Requirement: Máquina de Estados (RN-15)

The system MUST enforce a strict state machine for each `Comunicacion` row, rejecting invalid transitions at the service layer.

#### Scenario: Transición válida Pendiente a Enviando

- GIVEN a `Comunicacion` in state `Pendiente`
- WHEN the worker picks up the row for dispatch (`aprobado=True`)
- THEN the state MUST transition to `Enviando` before the SMTP call is made
- AND the transition MUST be committed to the database before sending

#### Scenario: Transición válida Pendiente a Cancelado

- GIVEN a `Comunicacion` in state `Pendiente`
- WHEN an authorized user with permission `comunicacion:aprobar` cancels it
- THEN the state MUST transition to `Cancelado`
- AND no further dispatch MAY occur

#### Scenario: Transición inválida desde estado terminal

- GIVEN a `Comunicacion` in state `Enviado` (terminal)
- WHEN any state transition is attempted
- THEN the system MUST raise `ServiceError`
- AND the row MUST remain in state `Enviado`

#### Scenario: No se puede cancelar un mensaje en vuelo

- GIVEN a `Comunicacion` in state `Enviando`
- WHEN a user attempts to cancel it
- THEN the system MUST raise `ServiceError` with HTTP 409
- AND the row MUST remain in state `Enviando`

---

### Requirement: Preview Obligatorio (F3.1, RN-16)

The system MUST provide a preview endpoint that renders subject and body templates with variable substitution, without persisting any data.

#### Scenario: Variables sustituidas correctamente

- GIVEN a subject template `"Hola $nombre, tenés $actividades_faltantes pendientes"`
- AND variables `{nombre: "Ana", actividades_faltantes: "TP1, TP2"}`
- WHEN `POST /api/v1/comunicaciones/preview` is called
- THEN the response MUST contain the rendered `asunto_renderizado` with variables replaced
- AND no row MUST be created in the `comunicacion` table

#### Scenario: Variable ausente no bloquea el preview

- GIVEN a template with variable `$materia`
- AND the variables dict does not include `materia`
- WHEN the preview is requested
- THEN the response MUST return the template with `$materia` left as a literal string
- AND the request MUST succeed with HTTP 200

---

### Requirement: Encolar Comunicaciones (F3.2)

The system MUST allow enqueueing one or more outbound communications, encrypting the recipient and generating a deterministic hash for future lookups.

#### Scenario: Envío a un destinatario individual

- GIVEN a valid `ComunicacionEnviarRequest` with one recipient
- WHEN `POST /api/v1/comunicaciones/` is called with permission `comunicacion:enviar`
- THEN one `Comunicacion` row MUST be created with `estado=Pendiente` and `lote_id=null`
- AND the `destinatario` column MUST store the AES-256 ciphertext (not plaintext)
- AND `destinatario_hash` MUST equal `generate_email_hash(email)`

#### Scenario: Envío masivo genera lote_id compartido

- GIVEN a `ComunicacionEnviarRequest` with 3 recipients
- WHEN the request is processed
- THEN 3 `Comunicacion` rows MUST be created sharing the same non-null `lote_id`
- AND each row MUST have `estado=Pendiente`

#### Scenario: Tenant con aprobación requerida

- GIVEN a tenant with `aprobacion_comunicaciones_masivas=True`
- AND a batch request (multiple recipients)
- WHEN the communications are enqueued
- THEN all rows MUST have `aprobado=False`
- AND the worker MUST NOT dispatch them until explicitly approved

#### Scenario: Identidad del remitente desde JWT

- GIVEN any enqueue request
- WHEN the row is created
- THEN `enviado_por` MUST equal `current_user.id` from the verified JWT
- AND MUST NOT be taken from the request body

---

### Requirement: Aprobación Humana (F3.3, RN-17)

The system MUST allow authorized users to approve communications before dispatch, at the batch or individual level.

#### Scenario: Aprobación de lote habilita despacho

- GIVEN a lote with 2 `Comunicacion` rows in state `Pendiente` with `aprobado=False`
- WHEN `POST /api/v1/comunicaciones/lotes/{lote_id}/aprobar` is called with `comunicacion:aprobar`
- THEN both rows MUST have `aprobado=True`
- AND the worker MUST be able to dispatch them on the next poll

#### Scenario: Aprobación sólo afecta filas Pendiente

- GIVEN a lote with 1 row in `Pendiente` and 1 row in `Enviado`
- WHEN the lote is approved
- THEN only the `Pendiente` row MUST have `aprobado` flipped to `True`
- AND the `Enviado` row MUST remain unchanged

#### Scenario: Aprobación individual es idempotente

- GIVEN a `Comunicacion` already in state `Enviado`
- WHEN individual approval is requested
- THEN the system MUST return HTTP 200 with the current row state
- AND MUST NOT raise an error

---

### Requirement: Cancelación

The system MUST allow cancelling pending communications before dispatch.

#### Scenario: Cancelación masiva de lote

- GIVEN a lote with 3 rows in state `Pendiente`
- WHEN `POST /api/v1/comunicaciones/lotes/{lote_id}/cancelar` is called
- THEN all 3 rows MUST transition to `Cancelado`
- AND the worker MUST NOT dispatch them

#### Scenario: No se puede cancelar un mensaje ya enviado

- GIVEN a `Comunicacion` in state `Enviado`
- WHEN individual cancellation is requested
- THEN the system MUST raise `ServiceError`
- AND the caller MUST receive HTTP 409

---

### Requirement: Worker Asíncrono y Crash Recovery

The system MUST dispatch pending approved communications via an async worker, with crash recovery on startup.

#### Scenario: Despacho exitoso Pendiente a Enviado

- GIVEN a `Comunicacion` in state `Pendiente` with `aprobado=True`
- WHEN the worker's `dispatch_one` is called
- THEN the row MUST transition to `Enviando` (committed before SMTP)
- AND after successful SMTP dispatch the row MUST transition to `Enviado`
- AND `enviado_at` MUST be set to the dispatch timestamp
- AND an `AuditLog` entry with `accion="COMUNICACION_ENVIAR"` MUST be created

#### Scenario: Filas no aprobadas no son despachadas

- GIVEN a `Comunicacion` in state `Pendiente` with `aprobado=False`
- WHEN the worker runs a poll cycle
- THEN the row MUST NOT be picked up by `list_dispatchable`
- AND the SMTP transport MUST NOT be called

#### Scenario: Reintento acotado en fallo de SMTP

- GIVEN a `Comunicacion` with `intentos=0` and `max_intentos=3`
- WHEN the SMTP dispatch fails on the first attempt
- THEN `intentos` MUST be incremented to 1
- AND the row MUST transition back to `Pendiente` for retry

#### Scenario: Error terminal al agotar reintentos

- GIVEN a `Comunicacion` with `intentos=2` and `max_intentos=3`
- WHEN the SMTP dispatch fails
- THEN `intentos` MUST be incremented to 3
- AND the row MUST transition to `Error` (terminal for automatic retry)
- AND no further automatic dispatch MUST occur

#### Scenario: Crash recovery al arrancar el worker

- GIVEN 2 `Comunicacion` rows in state `Enviando` (process died mid-dispatch)
- WHEN the worker starts up
- THEN both rows MUST be moved to `Pendiente` before entering the poll loop
- AND no SMTP call MUST be made during recovery

---

### Requirement: Auditoría de Envío

The system MUST write an immutable audit log entry for every successful dispatch, and MUST NOT write one on failure.

#### Scenario: Despacho exitoso genera AuditLog

- GIVEN a successful SMTP dispatch
- WHEN the worker transitions the row to `Enviado`
- THEN an `AuditLog` row MUST exist with `accion="COMUNICACION_ENVIAR"`, `actor_id=enviado_por`, `materia_id`, `filas_afectadas=1`

#### Scenario: Despacho fallido no genera AuditLog

- GIVEN a failed SMTP dispatch
- WHEN the worker handles the exception
- THEN no `AuditLog` row MUST be created for that dispatch attempt

---

### Requirement: Invariante de Cifrado del Destinatario

The system MUST ensure the recipient's email is never exposed in API responses or logs.

#### Scenario: ComunicacionResponse no expone destinatario

- GIVEN the `ComunicacionResponse` Pydantic schema
- WHEN inspecting `model_fields`
- THEN the field `destinatario` MUST NOT be present
- AND `destinatario_hash` MUST be present

#### Scenario: Columna destinatario almacena ciphertext

- GIVEN a `Comunicacion` row created with a plaintext email
- WHEN the `destinatario` column is read directly from the database via raw SQL
- THEN the value MUST be ciphertext (not the original plaintext email)
- AND decrypting it via `decrypt_attr` MUST return the original email
