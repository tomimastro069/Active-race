# equipos-exportacion Specification

## Purpose
Define the export functionality for teaching teams, allowing coordinators and administrators to download a structured list of team assignments.

## Requirements

### Requirement: Export Team to File
The system MUST export all active assignments for a given academic context to a structured file format (e.g., CSV or JSON) for external use.

#### Scenario: Successful export
- GIVEN a valid academic context with one or more assignments
- WHEN a coordinator requests an export
- THEN the system MUST generate and return a file containing the team's details (user names, roles, validity).

#### Scenario: Export empty team
- GIVEN a valid academic context with no assignments
- WHEN a coordinator requests an export
- THEN the system MUST return an empty structured file or a clear indication that no records exist.
