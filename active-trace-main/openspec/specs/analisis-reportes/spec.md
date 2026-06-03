# analisis-reportes Specification

## Purpose

This specification defines the behavior of the Analytics and Reporting module (F2.2–F2.9), which allows teachers, tutors, and administrators to track student progress, identify delayed students based on subject thresholds (RN-06), rank approved activities (RN-09), export ungraded submissions (RN-07, RN-08), and monitor activity across cohorts.

## Requirements

### Requirement: Identify Delayed Students

The system MUST identify students who are delayed based on missing activities or grades below the subject's numerical threshold (RN-06).

#### Scenario: Student has missing qualitative grade
- GIVEN a subject with required qualitative activities
- WHEN the student has submitted the activity but `finalizado` is false or `nota_textual` is null
- THEN the student is considered delayed

#### Scenario: Student has grade below numeric threshold
- GIVEN a subject with a numeric threshold of 60
- WHEN the student receives a `nota_numerica` of 50 on a required activity
- THEN the student is considered delayed

### Requirement: Rank Approved Activities

The system MUST calculate and rank students by the count of their approved activities within a cohort (RN-09).

#### Scenario: Valid ranking generation
- GIVEN students with varying numbers of approved activities
- WHEN the ranking report is requested
- THEN the students are ordered descending by their approved count
- AND students with 0 approved activities MUST NOT be included in the ranking

### Requirement: Export Ungraded Practical Assignments (TPs)

The system MUST allow exporting a list of submitted but ungraded qualitative assignments (RN-07, RN-08).

#### Scenario: Exporting pending qualitative submissions
- GIVEN students who submitted assignments where `es_numerica` is false, `finalizado` is true, but `nota_textual` is null
- WHEN the export is requested
- THEN the system returns the list of those specific pending submissions

### Requirement: Quick Metrics and Final Grades

The system MUST provide aggregated metrics and grouped final grades for a subject.

#### Scenario: Quick subject report
- GIVEN a subject with multiple activities
- WHEN the quick report is requested
- THEN the system returns the total enrolled students, total submissions, and average approval rate

#### Scenario: Final grades grouping
- GIVEN a cohort with multiple completed activities
- WHEN the final grades report is requested
- THEN the system groups grades by student, showing their final status per activity

### Requirement: Multi-Filter Activity Monitor

The system MUST provide activity monitors that can be filtered by role context (F2.7, F2.8, F2.9).

#### Scenario: Teacher views their commission
- GIVEN a user with `atrasados:ver_propio` assigned to a specific `materia_id`
- WHEN they request the monitor
- THEN the results MUST be restricted to their assigned students

#### Scenario: Admin views all cohorts in a date range
- GIVEN a user with `atrasados:ver` and no restricted context
- WHEN they request the monitor with `desde_fecha` and `hasta_fecha`
- THEN the results show all activities in the system within that date range
