# Fix 06 — MissingGreenlet en mensajería interna (C-20): lazy-load en contexto async

## Why

`POST /api/v1/inbox/threads` responde 500 (`sqlalchemy.exc.MissingGreenlet`). El service
construye la respuesta con `thread_to_response(thread)` sobre una instancia recién creada cuya
relación `mensajes` nunca fue cargada: el acceso dispara un lazy-load síncrono, prohibido bajo
`AsyncSession`/asyncpg. `POST /inbox/thread/{id}/reply` tiene el mismo defecto con
`message.remitente` en `message_to_response`.

El bug estaba enmascarado: el test `test_c20_perfil_y_mensajeria.py::test_mensajeria_endpoints`
fallaba antes con el 401 del `TenantMiddleware` (ver fix-01) sin llegar a ejecutar el handler.
Los paths de lectura (`GET /inbox/threads`, `GET /inbox/thread/{id}`) no están afectados porque
el repository precarga con `selectinload`.

## What Changes

- `MensajeriaService.create_thread` devuelve el hilo recargado vía
  `repo.get_thread_by_id_and_member(thread.id, creador_id)` (precarga `miembros` y
  `mensajes → remitente`, con scope de tenant), en lugar de la instancia transient.
- `MensajeriaService.reply_to_thread` precarga la relación `remitente` del mensaje recién
  persistido con `await session.refresh(message, ["remitente"])` antes de devolverlo.
- Sin cambios de schema, API ni migraciones; los routers no cambian.

## Impact

- `backend/app/services/mensajeria.py`
- Tests: `test_c20_perfil_y_mensajeria.py::test_mensajeria_endpoints` pasa; la suite completa
  queda en verde (181/181).
