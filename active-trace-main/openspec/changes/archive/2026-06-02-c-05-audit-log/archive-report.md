# Archive Report: C-05 Audit Log & Impersonación

## 1. Resumen Ejecutivo
**Estado:** COMPLETO y ARCHIVADO
Se implementó exitosamente el módulo de auditoría (`AuditLog`) y el mecanismo de impersonación (suplantación de identidad controlada y auditable) para administradores.

## 2. Decisiones Técnicas y Arquitectura Consolidada
* **Inmutabilidad (Append-Only):** Se forzó a nivel DB mediante el uso de Triggers de Postgres (`prevent_audit_log_modification`), impidiendo cualquier `UPDATE`, `DELETE` o `TRUNCATE` sobre la tabla `audit_log`. 
* **Atribución de Responsabilidad (Golden Rule):** Se modificó el esquema de JWT para soportar un claim adicional `impersonated_sub`.
* **Middlewares / Guards:** El método `get_current_user` inyecta ahora el `actor_id` (quien ejecuta la acción) y el `impersonado_id` (quien recibe la acción) directamente en el `request.state`. Esto permite un acoplamiento nulo con la lógica de negocio; el `AuditService` absorbe estos IDs de forma transparente.

## 3. Pruebas y Validación
Se diseñaron pruebas de integración (E2E) que garantizan que el comportamiento se ajusta a lo especificado. Durante las pruebas se validó que:
* Las modificaciones directas a través de un repositorio sobre `AuditLog` lancen errores.
* Las modificaciones intentadas por fuera (a nivel SQL) reboten contra el Trigger.
* La ruta de impersonación genera los JWT correctos.
* Los endpoints autorizados reportan fielmente quién hizo qué (y por cuenta de quién).

## 4. Archivos Clave Modificados/Creados
* `backend/app/models/audit_log.py` (Nuevo)
* `backend/app/repositories/audit_log.py` (Nuevo)
* `backend/app/services/audit.py` (Nuevo)
* `backend/alembic/versions/004_audit_log.py` (Migración con Triggers)
* `backend/app/core/security.py` (Modificación de payload JWT)
* `backend/app/core/dependencies.py` (Ajustes a `get_current_user` y context vars)
* `backend/app/api/v1/routers/auth.py` (Endpoint `/impersonate`)
* `backend/tests/test_audit.py` (Tests de integración)

## 5. Cierre
El código queda integrado y funcional. Se demostró madurez en la elección de soluciones agnósticas (no tocar la firma de cada caso de uso para inyectar auditabilidad) respetando la Clean Architecture base del proyecto.
