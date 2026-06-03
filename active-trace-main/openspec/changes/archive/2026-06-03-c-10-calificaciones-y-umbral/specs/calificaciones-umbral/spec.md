# Calificaciones y Umbral Specification

## Purpose
Define the behavior for tracking student grades, detecting ungraded deliveries, and establishing customizable approval thresholds per subject and teacher.

## Requirements

### Requirement: Import Grades from CSV
The system MUST allow teachers and coordinators to import grades from a CSV file. The system MUST identify numerical grade columns using the `(Real)` suffix. The system MUST associate each grade row to a student using the `email` column matched against the active `VersionPadron` for the selected subject and cohort.

#### Scenario: Successful import of numerical grades
- GIVEN a CSV containing email and an activity column "Examen (Real)"
- WHEN the user imports the file
- THEN the system creates a `Calificacion` for the student with `es_numerica=True` and `nota_numerica` set to the value
- AND `finalizado` is set to `True`

### Requirement: Calculate Approval Status
The system MUST determine the `aprobado` boolean field for each `Calificacion` upon import or threshold change. If `es_numerica` is True, it MUST compare `nota_numerica` against the active `UmbralMateria.umbral_pct` (default 60%). If `es_numerica` is False, it MUST check if `nota_textual` is within `UmbralMateria.valores_aprobatorios` (default "Satisfactorio", "Supera lo esperado").

#### Scenario: Numerical grade passes default threshold
- GIVEN a `Calificacion` with `nota_numerica` 70 and default threshold 60
- WHEN approval is evaluated
- THEN `aprobado` is set to `True`

#### Scenario: Textual grade fails default threshold
- GIVEN a `Calificacion` with `nota_textual` "No Satisfactorio"
- WHEN approval is evaluated
- THEN `aprobado` is set to `False`

### Requirement: Import Finalization Report
The system MUST allow importing a completion report CSV to detect ungraded qualitative activities. The system MUST update existing `Calificacion` records or create new ones with `finalizado=True` and `es_numerica=False` when an activity is marked completed in the report.

#### Scenario: Detecting an ungraded qualitative activity
- GIVEN a student who has completed "TP1" in the completion report but has no grade
- WHEN the report is imported
- THEN a `Calificacion` is created with `finalizado=True`, `es_numerica=False`, and `nota_textual` as `NULL`

### Requirement: Isolate Grade Clearing
The system MUST restrict grade deletion operations (vaciado) strictly to the grades imported by the user executing the action, satisfying RN-04.

#### Scenario: Clearing grades for a subject
- GIVEN a teacher who imported grades for "Materia A"
- WHEN the teacher executes the vaciado operation for "Materia A"
- THEN only `Calificacion` records associated with the teacher are logically deleted
- AND grades imported by other teachers for the same subject remain untouched
