# guardias-gestion Specification

## Purpose

Registro y seguimiento de disponibilidad horaria para guardias y tutorías de acompañamiento estudiantil.

## Requirements

### Requirement: Registrar Guardia

El sistema MUST permitir a un usuario autorizado registrar un bloque de guardia en el sistema.

#### Scenario: Registro exitoso por tutor

- GIVEN un tutor con asignación vigente y permisos `encuentros:gestionar`
- WHEN registra una guardia para los días Martes de 14:00 a 14:45
- THEN el sistema MUST crear el registro de Guardia asociado a su asignación y la materia
- AND el estado inicial MUST ser `Pendiente`

### Requirement: Consultar Guardias Globales

El sistema MUST permitir a la coordinación listar y filtrar todas las guardias del tenant.

#### Scenario: Consulta de coordinación

- GIVEN un coordinador
- WHEN solicita el listado de guardias
- THEN el sistema MUST devolver solo las guardias pertenecientes a su tenant, filtrables por materia o cohorte.
