# asignacion-contextual Specification

## Purpose

Provide CRUD REST APIs for assigning roles to users within specific academic contexts (materia, carrera, cohorte, comision).

## Requirements

### Requirement: Manage Assignments API

The system MUST provide an `/api/asignaciones` endpoint for authorized users (with `equipos:asignar` permission) to create, list, and modify assignments.

#### Scenario: Authorized creation
- GIVEN a user with `equipos:asignar` permission
- WHEN they send a POST to `/api/asignaciones` with valid context data
- THEN the assignment is created successfully.

#### Scenario: Unauthorized access
- GIVEN a user without `equipos:asignar` permission
- WHEN they access `/api/asignaciones`
- THEN the system MUST return 403 Forbidden.
