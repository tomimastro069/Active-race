# equipos-gestion-masiva Specification

## Purpose
Define the behavior for mass operations on teaching teams, including mass assignment, team cloning between cohorts, and mass validity updates.

## Requirements

### Requirement: Mass Assignment
The system MUST support assigning multiple users to a specific academic context (materia, carrera, cohorte) with a specific role and validity period in a single operation.

#### Scenario: Successful mass assignment
- GIVEN a list of valid user IDs and a valid academic context
- WHEN a coordinator requests a mass assignment
- THEN the system MUST create assignments for all provided users
- AND the system MUST generate an audit log entry for the mass assignment operation.

#### Scenario: Invalid user in mass assignment
- GIVEN a list of user IDs where at least one is invalid
- WHEN a mass assignment is requested
- THEN the system MUST reject the entire operation (transactional)
- AND return an error indicating the invalid user.

### Requirement: Team Cloning
The system MUST allow cloning all active assignments from a source academic context to a destination academic context.

#### Scenario: Successful team clone
- GIVEN a source context (e.g., Cohorte A) with active assignments and a destination context (e.g., Cohorte B) with no active assignments
- WHEN a coordinator requests to clone the team
- THEN the system MUST duplicate all active assignments into the destination context
- AND the system MUST generate an audit log entry.

#### Scenario: Destination context already has assignments
- GIVEN a destination context that already has active assignments
- WHEN a clone operation is requested
- THEN the system MUST reject the operation to prevent overlapping
- AND return a conflict error.

### Requirement: Mass Validity Update
The system MUST allow updating the `desde` and `hasta` validity dates for all assignments within a specific academic context.

#### Scenario: Successful mass validity update
- GIVEN a valid academic context with existing assignments
- WHEN a coordinator requests to update the validity dates
- THEN the system MUST update the dates for all matching assignments
- AND the system MUST generate an audit log entry.
