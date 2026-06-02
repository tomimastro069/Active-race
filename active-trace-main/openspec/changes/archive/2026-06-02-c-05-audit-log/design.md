# Design Document — C-05: audit-log

## Context

activia-trace es un sistema crítico ("CRITICO" en Governance) que maneja datos académicos y personales. El sistema requiere un **Log de Auditoría (E-AUD)** inmutable que registre de manera fehaciente toda acción significativa (importación de calificaciones, cambios de estado, etc.). A su vez, se requiere una funcionalidad de **Impersonación** para que administradores o soporte técnico puedan operar temporalmente como otro usuario, pero con la condición estricta de que toda acción quede atribuida en la auditoría al "actor real" (quien impersona).

## Goals / Non-Goals

**Goals:**
- Diseñar e implementar el modelo `AuditLog` (append-only) para registrar `actor_id`, `impersonado_id`, `accion`, `materia_id`, IP, y detalles en JSON.
- Implementar defensas en profundidad (app y base de datos) para evitar `UPDATE` y `DELETE` sobre la tabla de auditoría.
- Implementar un servicio/helper que facilite el registro estructurado de auditoría.
- Implementar el mecanismo de **Impersonación** emitiendo un JWT especial que contenga `sub` (actor real) e `impersonated_sub` (suplantado).
- Implementar endpoints para iniciar la impersonación (protegidos por el permiso `impersonacion:usar`).

**Non-Goals:**
- Construir la interfaz de usuario (frontend) para visualizar los logs de auditoría (→ panel C-19).
- Loguear acciones de lectura estándar (GET), a menos que involucren acceso a datos altamente sensibles que la normativa exija registrar.

## Decisions

### D1 — Inmutabilidad garantizada (Append-Only)

**Decisión**: El repositorio de `AuditLog` debe lanzar excepciones si se invocan los métodos `update` o `delete`. Adicionalmente, el modelo base de `AuditLog` no heredará los timestamps de `deleted_at` para no soportar soft-deletes.

**Alternativas consideradas**:
- ❌ Guardar logs en archivos de texto: no permite consultas relacionales fáciles en el backend para reportes nativos.
- ✅ Almacenar en la BD relacional blindando la tabla y la capa de acceso a datos contra modificaciones lógicas.

### D2 — Representación de Impersonación en JWT

**Decisión**: La identidad real y la impersonada viajan juntas en el payload del token JWT de acceso temporal.
- `sub`: ID del actor real.
- `impersonated_sub`: ID del usuario impersonado (opcional).

**Rationale**: De esta manera, el middleware de autenticación no tiene que hacer queries adicionales complejas para saber si la request está bajo impersonación. La función `get_current_user` procesará este JWT y la capa de servicio tendrá disponible tanto al actor real como al suplantado.

### D3 — Inyección Transversal del Contexto (IP, User-Agent)

**Decisión**: Usaremos las capacidades nativas de FastAPI (`Request`) extraídas mediante una dependencia para obtener el IP y User-Agent y pasarlo al `AuditService`. 

## Data Model

### Tabla `audit_log`
- `id`: UUID (PK, auto)
- `tenant_id`: UUID (FK a tenant, not null)
- `fecha_hora`: DateTime (not null, default now UTC)
- `actor_id`: UUID (FK a usuario real, not null)
- `impersonado_id`: UUID (FK a usuario suplantado, nullable)
- `materia_id`: UUID (FK a materia, nullable)
- `accion`: String(100) (not null, e.g. `IMPERSONACION_INICIAR`, `CALIFICACIONES_IMPORTAR`)
- `detalle`: JSONB (nullable, contexto adicional)
- `filas_afectadas`: Integer (nullable)
- `ip`: String(50) (nullable)
- `user_agent`: String(255) (nullable)
