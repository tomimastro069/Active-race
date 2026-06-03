# Delta for user-academic-assignment-e5

## MODIFIED Requirements

### Requirement: E5 Asignacion (User Role Context Mapping)

The system SHALL support mapping users to roles within specific academic contexts (such as carreras, cohortes, materias, or comisiones) with temporal constraints (`desde` and `hasta`). The system MUST expose a derived property `estado_vigencia` indicating if the assignment is currently active ("Vigente" or "Vencida").
(Previously: The system only supported the mapping without exposing a derived property for vigencia)

#### Scenario: Active assignment resolution
- GIVEN an assignment valid from '2026-06-01' to '2026-06-30'
- WHEN the system evaluates permissions on '2026-06-15'
- THEN the assignment is active and its permissions are granted
- AND `estado_vigencia` SHALL be "Vigente".

#### Scenario: Expired assignment resolution
- GIVEN an assignment that ended on '2026-05-31'
- WHEN the system evaluates permissions on '2026-06-01'
- THEN the assignment is inactive and no permissions from it are granted
- AND `estado_vigencia` SHALL be "Vencida".
