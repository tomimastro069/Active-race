# Proposal: C-11 analisis-atrasados-reportes

## Intent

Implement the Epic 2 reporting and analytics capabilities (F2.2–F2.9), allowing teachers and coordinators to compute delayed students, view ranked activities, and export ungraded practical assignments (TPs). This addresses the need to monitor student progress and enforce business rules (RN-06 to RN-09) dynamically.

## Scope

### In Scope
- Computation of delayed students based on missing activities or grades below the subject threshold.
- Ranking of approved activities for students (excluding those with 0 approvals).
- Grouped final grades and subject summary metrics (quick reports).
- Export of qualitative ungraded practical assignments (TPs).
- Multi-filter activity monitors (general, tutor/professor tracking, and admin date-range tracking).
- API endpoints under `/api/analisis/*` protected by `atrasados:ver` and `atrasados:ver_propio`.
- Service layer methods encapsulating business logic, strictly decoupling data access in repositories.

### Out of Scope
- Modifications to database schemas (existing `Calificacion` and `UmbralMateria` models will be used).
- Adding new roles to RBAC (we rely on the existing permission `atrasados:ver`).
- Asynchronous task queueing for report generation (synchronous API responses are expected).

## Capabilities

### New Capabilities
- `analisis-reportes`: API endpoints and service logic for calculating delayed students, tracking approvals, fetching grading metrics, exporting ungraded TPs, and general activity monitoring for Epic 2.

### Modified Capabilities
- None

## Approach

Create a dedicated `AnalisisService` to implement all Epic 2 metrics and computations (F2.2 to F2.9). Repositories (`calificacion.py`, `padron_repository.py`) will be extended with helper methods to fetch the necessary data efficiently. An API router `analisis.py` will expose the data through protected endpoints mapping to the UI monitor requirements.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/api/v1/routers/analisis.py` | New | New endpoints for reports and monitors |
| `backend/app/services/analisis_service.py` | New | Business logic for metrics and ranking |
| `backend/app/schemas/analisis.py` | New | Pydantic response models |
| `backend/app/repositories/calificacion.py` | Modified | Add helpers for ungraded TPs and distinct activity names |
| `backend/app/main.py` | Modified | Include the new `analisis` router |
| `backend/tests/` | New | Strict TDD tests for the API and Service layers |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Performance issues in large cohort rankings | Medium | Use optimized repository queries and DB-side grouping where appropriate |
| Edge cases in grading thresholds | Medium | Comprehensive Strict TDD tests covering RN-06 to RN-09 scenarios |

## Rollback Plan

Revert the PR commit for C-11. As no database schema migrations are being introduced, the rollback safely removes the new routes and services without risking data integrity.

## Dependencies

- C-10

## Success Criteria

- [ ] API successfully lists delayed students based on missing activities and thresholds.
- [ ] Rankings strictly exclude students with 0 approved activities.
- [ ] Export endpoint accurately returns ungraded qualitative TPs.
- [ ] All new logic passes Strict TDD validation.
