# Tareas Internas Specification

## Purpose
Define requirements for internal task tracking, delegation, and asynchronous communication threads between roles within a tenant.

## Requirements

### Requirement: Creacion de Tarea
The system MUST allow users with `tareas:gestionar` to create a task in their tenant. The task MUST record `asignado_a`, `asignado_por` (creator), `descripcion`, and optional references (`materia_id`, `contexto_id`). The initial state MUST be `Pendiente`.

#### Scenario: Creacion exitosa por Coordinador
- GIVEN a Coordinator with permission `tareas:gestionar` in tenant A
- WHEN creating a task for a tutor in tenant A with a valid description
- THEN the task is created with state `Pendiente`
- AND `asignado_por` matches the Coordinator's ID
- AND tenant_id matches tenant A.

#### Scenario: Creacion rechazada por Tenant Invalido
- GIVEN a Coordinator in tenant A
- WHEN trying to assign a task to a user in tenant B
- THEN the system MUST reject the creation with a validation error.

---

### Requirement: Listado y Acceso a Tareas
The system MUST enforce access control on task lists. Users with `tareas:gestionar` can view all tasks within their tenant. Users with `tareas:gestionar_propio` MUST only view tasks where they are `asignado_a` or `asignado_por`.

#### Scenario: Profesor ve solo sus tareas asignadas
- GIVEN a Professor with permission `tareas:gestionar_propio` (and not `tareas:gestionar`)
- WHEN requesting the list of tasks
- THEN the list only contains tasks where the Professor is `asignado_a` or `asignado_por`.

---

### Requirement: Transicion de Estado de Tareas
The system MUST allow the assignee (`asignado_a`) or a user with `tareas:gestionar` to change the task state between `Pendiente`, `En progreso`, `Resuelta`, and `Cancelada`.

#### Scenario: Cambio de estado exitoso
- GIVEN a task in state `Pendiente` assigned to a Tutor
- WHEN the Tutor updates the state to `En progreso`
- THEN the task state is updated in the database.

#### Scenario: Intento de cambio no autorizado
- GIVEN a task assigned to Tutor A
- WHEN Tutor B (without `tareas:gestionar`) attempts to change its state
- THEN the system MUST block the action with a 403 Forbidden error.

---

### Requirement: Comentarios en Tareas
The system MUST allow any user participating in a task (creator or assignee) or any user with `tareas:gestionar` to add comments.

#### Scenario: Agregar comentario al hilo
- GIVEN an active task assigned to Tutor A
- WHEN Tutor A adds a comment text
- THEN the comment is registered with the current timestamp and author ID.
