## 1. Modelos de Datos para RBAC

- [ ] 1.1 (RED) Escribir test que verifique la inicialización y persistencia de `Rol` con `tenant_id` nullable.
- [ ] 1.2 (RED) Escribir test que verifique la inicialización de `Permiso` y la relación intermedia `RolPermiso`.
- [ ] 1.3 (RED) Escribir test que valide la creación de `Asignacion` con vigencias (`desde`/`hasta`) y claves de contexto.
- [ ] 1.4 (GREEN) Implementar modelo `Rol` en `app/models/rol.py`.
- [ ] 1.5 (GREEN) Implementar modelo `Permiso` en `app/models/permiso.py`.
- [ ] 1.6 (GREEN) Implementar modelo `RolPermiso` en `app/models/rol_permiso.py`.
- [ ] 1.7 (GREEN) Implementar modelo `Asignacion` en `app/models/asignacion.py`.
- [ ] 1.8 (REFACTOR) Organizar los exports de los nuevos modelos en `app/models/__init__.py`.

## 2. Repositorios de Autorización

- [ ] 2.1 (RED) Escribir test que verifique la resolución de permisos por repositorio.
- [ ] 2.2 (GREEN) Implementar repositorios correspondientes (`RolRepository`, `PermisoRepository`, `AsignacionRepository`) bajo `app/repositories/`.
- [ ] 2.3 (GREEN) Implementar método optimizado en `AsignacionRepository` para obtener la unión de permisos activos vigentes de un usuario en un tenant.
- [ ] 2.4 (REFACTOR) Organizar los exports en `app/repositories/__init__.py`.

## 3. Dependency Guards en FastAPI

- [ ] 3.1 (RED) Escribir test unitario sobre `require_permission` que verifique que levanta 403 ante falta de permisos.
- [ ] 3.2 (GREEN) Implementar la función `require_permission` en `app/core/dependencies.py` que comprueba permisos en DB.
- [ ] 3.3 (GREEN) Adaptar `get_current_user` en `dependencies.py` para sincronizar la carga de roles del usuario.
- [ ] 3.4 (REFACTOR) Limpiar logs y optimizar consultas en el flujo de autenticación del router.

## 4. Migración Alembic y Seed de Matriz

- [ ] 4.1 (RED) Escribir test de migración que valide la existencia de las tablas `rol`, `permiso`, `rol_permiso` y `asignacion`.
- [ ] 4.2 (GREEN) Crear migración Alembic `003_rbac.py` con las definiciones y FKs correspondientes.
- [ ] 4.3 (GREEN) Implementar el seed inicial dentro de la migración con los roles semilla (`ADMIN`, `PROFESOR`, etc.) y sus correspondientes permisos según `03_actores_y_roles.md`.
- [ ] 4.4 (TRIANGULATE) Correr `alembic upgrade head` y validar esquema.

## 5. Tests de Integración de RBAC

- [ ] 5.1 (RED) Escribir caso de prueba: usuario intenta acceder a recurso protegido sin el permiso -> 403 Forbidden.
- [ ] 5.2 (RED) Escribir caso de prueba: usuario con múltiples asignaciones activas hereda la unión de todos los permisos.
- [ ] 5.3 (RED) Escribir caso de prueba: usuario con asignación vencida (`hasta` anterior a la fecha actual) no hereda los permisos del rol.
- [ ] 5.4 (RED) Escribir caso de prueba: el guard reconoce permisos con terminación `_propio` y los autoriza preliminarmente.
- [ ] 5.5 (GREEN) Crear `backend/tests/test_rbac.py` e implementar las pruebas unitarias y de integración.
- [ ] 5.6 (REFACTOR) Consolidar fixtures de datos de prueba en `tests/conftest.py` para simular roles y asignaciones rápidamente.

## 6. Verificación Final de la Fase

- [ ] 6.1 Correr la suite de pruebas completa y validar verde al 100%.
- [ ] 6.2 Verificar que ningún archivo modificado excede las 500 líneas de código.
