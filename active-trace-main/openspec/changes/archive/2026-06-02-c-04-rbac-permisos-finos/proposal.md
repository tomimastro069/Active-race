## Why

activia-trace requiere un sistema de autorización robusto, dinámico y acotado por tenant para cumplir con los requisitos del negocio. Actualmente, la autenticación (C-03) está completada, pero no hay control sobre qué recursos o acciones puede realizar un usuario autenticado. Para soportar múltiples perfiles académicos (como ALUMNO, PROFESOR, COORDINADOR) y restringir el acceso a datos e integraciones sensibles, es imprescindible contar con un motor de **Control de Acceso Basado en Roles (RBAC) con permisos finos**, acotado por vigencias temporales y scopes contextuales.

## What Changes

- **Modelos de Datos para RBAC**:
  - `Rol`: Entidad de catálogo para los perfiles del sistema (`ADMIN`, `PROFESOR`, `COORDINADOR`, etc.).
  - `Permiso`: Entidad para las acciones atómicas del tipo `modulo:accion`.
  - `RolPermiso`: Tabla intermedia para la asociación dinámica de capacidades.
  - `Asignacion`: Entidad de dominio (E5) que conecta un `Usuario` con un `Rol` dentro de un contexto académico, acotado por fechas `desde` y `hasta`.
- **Rutinas de Autorización en el Ciclo de Request**:
  - Un cargador/caching en memoria o consultas optimizadas en base de datos para resolver los permisos efectivos del usuario en cada petición (unión de permisos de sus roles vigentes).
  - Implementación de la dependencia `require_permission("modulo:accion")` para su uso como guard en endpoints de FastAPI.
- **Base de Datos & Seed de Matriz**:
  - Migración Alembic `003` para crear las tablas de RBAC.
  - Seed de datos para poblar la matriz inicial de permisos detallada en la especificación de dominio (`03_actores_y_roles.md`).
- **Tests Unitarios y de Integración**:
  - Pruebas que validen el rechazo 403 ante permisos insuficientes, la vigencia temporal de asignaciones, y la distinción de permisos globales vs. limitados a ámbito propio.

## Capabilities

### New Capabilities

- `rbac-catalog-models`: Tablas administrables en DB para `Rol`, `Permiso` y la intermedia `RolPermiso`.
- `user-academic-assignment-e5`: Entidad `Asignacion` (E5) para relacionar usuario, rol, contexto académico y rango de vigencia temporal.
- `require-permission-guard`: Guard de seguridad/dependencia para FastAPI (`require_permission("modulo:accion")`) que intercepta la request y valida los permisos efectivos.
- `effective-permissions-resolver`: Resolvedor server-side que computa la unión de permisos de todos los roles vigentes del usuario acotado al tenant actual.
- `rbac-seed-migration`: Migración Alembic `003` que crea la estructura de datos y carga la matriz por defecto para los roles semilla.

### Modified Capabilities

- `auth-current-user-claims`: Ajuste de la carga de usuario actual para resolver dinámicamente los roles asociados a las asignaciones vigentes e inyectarlos en la firma.

## Impact

- **Código y Arquitectura**: Modificación de `backend/app/core/dependencies.py` para incluir el guard `require_permission`, creación de nuevos modelos y repositorios en `app/models/` y `app/repositories/`.
- **Base de Datos**: Creación de 4 tablas nuevas (`rol`, `permiso`, `rol_permiso`, `asignacion`) con sus respectivos índices para acelerar la resolución de permisos.
- **Rendimiento**: La resolución de permisos debe ser altamente eficiente para no impactar la latencia de la API en cada request (se propone un select con join optimizado).
- **Gobernanza**: CRÍTICO. El control de acceso es fundamental para la seguridad del sistema y el aislamiento multi-tenant.
