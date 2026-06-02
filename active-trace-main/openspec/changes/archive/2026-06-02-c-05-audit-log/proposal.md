# C-05: Audit Log & Impersonación (Propuesta)

## 1. Resumen Ejecutivo
Implementar el registro de auditoría (E-AUD) append-only y el sistema de impersonación (suplantación legítima). El log de auditoría es inmutable a nivel aplicación y base de datos, garantizando trazabilidad y cumplimiento de gobierno. La impersonación permite a administradores y soporte operar en nombre de otro usuario, registrando de forma transparente tanto al actor real como al usuario impersonado en el log de auditoría.

## 2. Alcance (Scope)
- **Modelo `AuditLog` (E-AUD)**: Registro append-only en la base de datos con los campos requeridos (`actor_id`, `impersonado_id`, `materia_id`, `accion`, `detalle` JSON, `filas_afectadas`, `ip`, `user_agent`, `fecha_hora`).
- **Inmutabilidad Absoluta**: Prohibición estricta de `UPDATE` y `DELETE` en el modelo y repositorio de `AuditLog`.
- **Servicio/Helper de Auditoría**: Implementación de un servicio centralizado o dependencia de FastAPI para inyectar auditoría en endpoints y acciones significativas (ej. `CALIFICACIONES_IMPORTAR`).
- **Flujo de Impersonación**: 
  - Endpoints para iniciar y finalizar impersonación.
  - Generación de un JWT específico de impersonación.
  - Validación del permiso `impersonacion:usar`.
  - Atribución de acciones al actor real en la auditoría.
- **Migración de BD**: `004_audit_log.py`.
- **Tests**: Validación de append-only (rechazo de update/delete), tests de atribución bajo impersonación y verificación de permisos.

## 3. Decisiones Arquitectónicas

### 3.1 Inmutabilidad del Audit Log (Defensa en Profundidad)
- **Nivel Aplicación**: El `AuditLogRepository` sobreescribirá los métodos `update` y `delete` para lanzar excepciones de forma preventiva.
- **Nivel Base de Datos**: Como defensa en profundidad, agregaremos triggers en PostgreSQL para rechazar cualquier `UPDATE` o `DELETE` sobre la tabla `audit_log`, garantizando que ni siquiera accesos directos a la BD puedan alterar la traza.

### 3.2 Representación de la Impersonación (JWT y Estado)
Para manejar la impersonación de forma segura y auditable:
- El payload del JWT se extenderá. Un JWT normal tiene `sub` (el ID del usuario). Un JWT de impersonación tendrá `sub` (el ID del actor real que inició sesión) y un claim extra `impersonated_sub` (el ID del usuario al que se está suplantando).
- La dependencia `get_current_user` construirá un contexto de autenticación o inyectará la información en `request.state` para que la capa de servicios sepa que opera bajo impersonación y el Audit Log pueda registrar el `actor_id` (real) y el `impersonado_id`.

### 3.3 Captura de Contexto (IP, User-Agent)
Se utilizará una dependencia de FastAPI (`Depends`) para extraer la IP y el User-Agent del `Request` y pasarlos al servicio de auditoría, evitando que la capa de servicios de dominio dependa directamente del framework HTTP.

## 4. Riesgos y Mitigaciones
- **Vulnerabilidad**: Un atacante podría obtener un JWT de impersonación y operar de manera encubierta.
  - **Mitigación**: Exigir el permiso `impersonacion:usar` estrictamente al momento de solicitar el token. El JWT de impersonación tendrá un tiempo de expiración corto (menor a un token normal).
- **Crecimiento de la BD**: La tabla `audit_log` crecerá de forma monótonamente creciente.
  - **Mitigación**: Solo se auditarán "acciones significativas" (cambios de estado, accesos a PII, impersonación). No se registrarán accesos de lectura estándar (GETs) salvo que lo requiera normativas específicas.

## 5. Criterios de Aceptación
- La migración `004` crea la tabla con los triggers append-only.
- `AuditLogRepository` prohíbe `update` y `delete`.
- Existe un helper que facilita registrar acciones (con IP y User-Agent extraídos del request).
- Un usuario con `impersonacion:usar` puede generar un token de impersonación y toda acción que realice usando ese token se registra con su `actor_id` y el `impersonado_id` correspondiente.
