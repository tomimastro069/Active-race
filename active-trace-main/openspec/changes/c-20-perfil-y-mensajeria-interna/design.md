## Context

Actualmente, los usuarios no pueden autogestionar información sensible directamente desde la plataforma y la comunicación entre roles (tutores, docentes, admins) depende de canales fuera del sistema, lo que dificulta la trazabilidad y el control. El sistema tiene el modelo de Usuario cifrado pero carece de endpoints para editar el propio perfil o mensajería interna entre usuarios. Es un entorno estrictamente multi-tenant: cada operación se opera dentro del tenant y su autorización/identidad sólo se toma de sesión validada.

## Goals / Non-Goals

**Goals:**
- Permitir que cada usuario edite su propio perfil (menos CUIL); cambios auditados
- Soportar fiscales, bancarios, regional, modalidad de cobro
- Implementar mensajería interna entre usuarios con soporte de hilos y respuestas
- Garantizar visibilidad únicamente al usuario autenticado y a los destinatarios/autorizados
- Aislamiento estricto de tenant en todas las funciones (no cruzar datos)
- Exponer REST endpoints `/api/perfil` y `/api/inbox/*`

**Non-Goals:**
- No cubre cambios sobre la autenticación o tokens
- No permite editar roles ni asignaciones
- No afecta el sistema externo de comunicaciones a alumnos
- No habilita ni modifica auditoría (solo la utiliza)

## Decisions

- Se reutilizarán los modelos de datos de Usuario, sólo campos editables expuestos, CUIL como sólo lectura (inmutable por endpoint)
- El endpoint de edición válida sólo la sesión autenticada y solo sobre el propio usuario
- Mensajería interna modelada como `Thread` (hilo) y `Message` (mensaje en hilo), con visibilidad estricta a miembros del hilo; no hay mensajes broadcast ni públicos
- Los endpoints siempre filtran por tenant_id y usuario autenticado
- Se auditan todos los cambios de perfil o mensajes
- No se permite eliminar mensajes/hilos, sólo cierre lógico del hilo
- Se usan status HTTP estándar y respuestas JSON Pydantic strict
- Tests cubren edición, CUIL inmutable, mensajería aislada, acceso sólo a miembros del hilo

## Risks / Trade-offs

- [Error de filtrado de tenant/usuario] → Mitigación: Always scope every query by tenant_id and current user id
- [Edición accidental de CUIL u otros campos de sólo lectura] → Mitigación: Pydantic schemas con `extra='forbid'` y update validation server-side
- [Thread/message snooping cross-tenant] → Mitigación: Queries strictly filtered, all repo/services enforce tenant isolation
- [Baja cobertura de tests críticos] → Mitigación: Strict TDD mode, >80% coverage, edge cases on profile fields/modalities
- [Errores de sesión/identidad] → Mitigación: Identidad SIEMPRE desde la sesión validada JWT

## Migration Plan

- Deploy endpoints behind feature flag
- Roll out schema changes (if field-level control is new)
- Add tests and test with a tenant sandbox
- Enable for all users
- Rollback: disable feature flag and revert migrations

## Open Questions

- ¿Se permitirá búsqueda/selección de usuarios por nombre/email seguro para iniciar nuevos hilos de mensajes?
- ¿Se podrán cerrar hilos por usuario? (no delete, sólo closure lógico)
- ¿Auditar todos los cambios de perfil con nivel de campo o solo cambios existenciales?
