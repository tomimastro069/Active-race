## 1. Modelo de Datos y Migración (AuditLog)

- [ ] 1.1 (RED) Escribir test que verifique la inicialización de `AuditLog`.
- [ ] 1.2 (GREEN) Implementar modelo `AuditLog` en `app/models/audit_log.py`. No debe heredar los campos `is_deleted` o `deleted_at` ya que no aplica soft-delete.
- [ ] 1.3 (RED) Escribir test en `AuditLogRepository` comprobando que llamar a `update`, `delete` o `soft_delete` lanza `NotImplementedError` o `ValueError`.
- [ ] 1.4 (GREEN) Implementar `AuditLogRepository` en `app/repositories/audit_log.py` bloqueando la mutación.
- [ ] 1.5 (REFACTOR) Organizar los exports en `models/__init__.py` y `repositories/__init__.py`.
- [ ] 1.6 (GREEN) Generar la migración Alembic `004_audit_log.py` con las FKs y campos JSON correspondientes.

## 2. Inyección de Contexto (IP, User-Agent) y Audit Service

- [ ] 2.1 (RED) Escribir test unitario para `AuditService` verificando que invoca correctamente la persistencia append-only.
- [ ] 2.2 (GREEN) Implementar `AuditService` (`app/services/audit.py`) con el método `log_action(...)` parametrizado.
- [ ] 2.3 (GREEN) Implementar en `app/core/dependencies.py` un provider que reciba el `Request` y retorne un objeto de contexto o lo inyecte directamente.

## 3. Lógica de Impersonación y Modificaciones a Autenticación

- [ ] 3.1 (RED) Escribir test de generación y validación de JWT con payload de impersonación (`impersonated_sub`).
- [ ] 3.2 (GREEN) Modificar la creación de tokens en `app/core/security.py` y `app/services/auth.py` para tolerar el claim extra.
- [ ] 3.3 (RED) Escribir test para el dependency guard `get_current_user` simulando un token de impersonación y validando el contexto devuelto.
- [ ] 3.4 (GREEN) Actualizar `get_current_user` para que extraiga ambos usuarios de la base de datos (si corresponde) y los integre en el estado del request o en un DTO.
- [ ] 3.5 (GREEN) Implementar endpoint `POST /api/v1/auth/impersonate` en `routers/auth.py`. Debe requerir el guard `require_permission("impersonacion:usar")`.
- [ ] 3.6 (GREEN) Asegurar que el inicio de impersonación emita un log de auditoría automático (`IMPERSONACION_INICIAR`).

## 4. Pruebas de Integración y Verificación Final

- [ ] 4.1 (RED) Escribir test E2E: Admin con permisos inicia impersonación, recibe token, ejecuta acción, se verifica que el log de auditoría guarda `actor_id` (admin) e `impersonado_id` (suplantado).
- [ ] 4.2 (GREEN) Implementar y hacer pasar el test E2E en `backend/tests/test_audit_log.py` o anexo de autenticación.
- [ ] 4.3 Correr la suite completa y validar verde 100%.
- [ ] 4.4 Verificar reglas de linter y convenciones de equipo.
