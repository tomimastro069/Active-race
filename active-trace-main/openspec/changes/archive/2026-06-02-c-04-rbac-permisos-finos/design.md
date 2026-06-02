# Design Document — C-04: rbac-permisos-finos

## Context

activia-trace requiere asegurar sus endpoints basándose en un modelo de **Control de Acceso Basado en Roles (RBAC) con permisos finos**. El sistema es multi-tenant, lo que significa que el catálogo de roles y permisos debe ser personalizable por institución cliente, y los permisos efectivos de un usuario deben estar acotados a su tenant y a la vigencia temporal de sus asignaciones de rol en determinados contextos académicos.

## Goals / Non-Goals

**Goals:**
- Diseñar y crear las tablas de catálogo: `Rol`, `Permiso` y la intermedia `RolPermiso`.
- Diseñar y crear la tabla `Asignacion` (E5) que asocia un usuario con un rol, opcionalmente a un contexto académico (carrera, cohorte, materia, comisiones) y a un rango de fechas.
- Implementar la resolución de permisos efectivos del usuario combinando todas sus asignaciones vigentes.
- Proveer el guard `require_permission("modulo:accion")` para endpoints de FastAPI.
- Seedear la base de datos con los roles semilla (`ADMIN`, `PROFESOR`, `COORDINADOR`, `TUTOR`, `ALUMNO`, `NEXO`, `FINANZAS`) y sus permisos asociados.

**Non-Goals:**
- Implementar el portal del alumno o interfaces de visualización asociadas (→ C-06+).
- Implementar la lógica específica de dictado académico (comisiones, cohortes en detalle) más allá de sus claves foráneas en la asignación.
- Manejar la lógica de auditoría append-only para las asignaciones (→ C-05).

## Decisions

### D1 — Catálogo de seguridad parametrizable y tenant-scoped (nullable tenant_id)

**Decisión**: Las tablas `Rol` y `Permiso` tienen una columna `tenant_id` que admite valores nulos. 
- Si `tenant_id IS NULL`, representa definiciones por defecto provistas globalmente por el sistema (semillas inmutables).
- Si `tenant_id IS NOT NULL`, representa personalizaciones específicas del tenant.
La tabla de asignaciones (`Asignacion`) siempre requiere un `tenant_id` obligatorio.

**Alternativas consideradas**:
- ❌ Roles fijos hardcodeados en un Enum: impide que un tenant configure permisos personalizados.
- ❌ Duplicar filas de catálogo por cada tenant: genera redundancia innecesaria y hace complejas las actualizaciones globales.
- ✅ Roles administrables con tenant_id nullable: permite extensibilidad y personalización sin comprometer los valores por defecto.

### D2 — Resolución en caliente (server-side) de permisos efectivos

**Decisión**: En lugar de guardar los permisos del usuario en la sesión o en el JWT, se computa la unión de permisos vigentes en cada request haciendo un query optimizado a la base de datos a través de la asignación del usuario.
El JWT únicamente contendrá el claim mínimo de roles asignados.

**Rationale**: Almacenar permisos en el JWT causaría problemas de tamaño del token (bloating) e impediría la revocación instantánea o el cambio dinámico de permisos sin invalidar la sesión. La resolución en caliente garantiza consistencia de seguridad en tiempo real.

### D3 — Soporte para control contextual y sufijo `_propio`

**Decisión**: Cuando un usuario tiene un permiso restringido a su propio ámbito (ej: `atrasados:ver_propio`), el guard `require_permission` detecta el sufijo `_propio` en las capacidades del usuario, aprueba preliminarmente la request, y delega el filtro exacto de propiedad (ej. comprobar que el docente esté asignado a la materia o comision solicitada) al router o servicio correspondiente.

**Rationale**: La capa de dependencias HTTP (FastAPI) no tiene acceso al objeto de negocio específico de la base de datos antes de la ejecución de la lógica del endpoint. Delegar el cruce de propiedad al servicio/router mantiene el middleware desacoplado y eficiente.

### D4 — Rangos de vigencia temporal en UTC

**Decisión**: Las fechas `desde` y `hasta` en las asignaciones se contrastan con la hora UTC del servidor (`datetime.utcnow()`). Si `hasta` es nulo, la vigencia es abierta.
La query de resolución descarta inmediatamente cualquier asignación fuera de este rango de tiempo.

---

## Data Model

```
 ┌──────────┐         ┌──────────────┐         ┌─────────────┐
 │  Rol     │◄───────┤  RolPermiso  ├────────►│  Permiso    │
 └────▲─────┘         └──────────────┘         └─────────────┘
      │
      │ 1
      │
      │ *
 ┌────┴─────┐
 │Asignacion│◄─────── Usuario
 └──────────┘
```

### Tabla `rol`
- `id`: UUID (PK, auto)
- `tenant_id`: UUID (FK a tenant, nullable)
- `nombre`: String(100), not null
- `descripcion`: String(255)
- Timestamps & Soft Delete

### Tabla `permiso`
- `id`: UUID (PK, auto)
- `tenant_id`: UUID (FK a tenant, nullable)
- `nombre`: String(100), not null (e.g. `calificaciones:importar`)
- `descripcion`: String(255)
- Timestamps & Soft Delete

### Tabla `rol_permiso`
- `id`: UUID (PK, auto)
- `tenant_id`: UUID (FK a tenant)
- `rol_id`: UUID (FK a rol, cascade)
- `permiso_id`: UUID (FK a permiso, cascade)
- Timestamps & Soft Delete

### Tabla `asignacion`
- `id`: UUID (PK, auto)
- `tenant_id`: UUID (FK a tenant)
- `usuario_id`: UUID (FK a usuario, cascade)
- `rol_id`: UUID (FK a rol)
- `materia_id`: UUID (nullable)
- `carrera_id`: UUID (nullable)
- `cohorte_id`: UUID (nullable)
- `comisiones`: String (lista de comisiones, nullable)
- `responsable_id`: UUID (FK a usuario, nullable)
- `desde`: DateTime, not null
- `hasta`: DateTime (nullable)
- Timestamps & Soft Delete
