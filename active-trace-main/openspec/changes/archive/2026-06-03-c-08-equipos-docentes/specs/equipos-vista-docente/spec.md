# equipos-vista-docente Specification

## Purpose
Define the behavior for the "mis-equipos" view, ensuring teachers can securely view their own assignments without exposing data from other users.

## Requirements

### Requirement: Scoped Team View
The system MUST return only the assignments that belong to the currently authenticated user when the "mis-equipos" endpoint is queried.

#### Scenario: Teacher viewing their own teams
- GIVEN an authenticated user (Teacher) with assignments in multiple contexts
- WHEN the user requests their teams
- THEN the system MUST return only the assignments where the `usuario_id` matches the authenticated user's ID.

#### Scenario: Prevention of data leakage
- GIVEN an authenticated user
- WHEN the user attempts to pass another user's ID as a parameter to the "mis-equipos" endpoint
- THEN the system MUST ignore the parameter
- AND MUST strictly return only the authenticated user's assignments.
