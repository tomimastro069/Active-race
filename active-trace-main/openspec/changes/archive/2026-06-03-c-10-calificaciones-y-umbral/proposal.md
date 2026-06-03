# Proposal: c-10-calificaciones-y-umbral

## Intent
Address grade tracking and course module completion analysis, allowing teachers to identify student risk using configurable grade approval thresholds (umbral).

## Scope

### In Scope
- Database models `Calificacion` (E7) and `UmbralMateria` (E8) in SQLAlchemy.
- CSV parsing utility for qualifications (detect `(Real)` columns for numeric, others for textual) and finalization reports (cross-ref with grades).
- Service logic to compute `aprobado` based on numeric threshold (configured or tenant default 60%) or qualitative scales (configured or default `["Satisfactorio", "Supera lo esperado"]`).
- API endpoints:
  - `POST /api/v1/calificaciones/preview`: parses grades CSV, returns detected activities.
  - `POST /api/v1/calificaciones/import`: imports grades for selected activities.
  - `POST /api/v1/calificaciones/import-finalizacion`: imports finalization CSV, matching active padron.
  - `POST /api/v1/calificaciones/vaciar`: clears grades uploaded by active teacher for a subject (RN-04).
  - `GET/POST /api/v1/calificaciones/umbral`: configures custom threshold.
- Alembic database migration.

### Out of Scope
- Frontend UI components or pages (deferred to FASE 5, C-22).
- PDF or Excel report generation (deferred to C-11).

## Capabilities

### New Capabilities
- `calificaciones-umbral`: Gestión de calificaciones e ingesta de notas del LMS con configuración de umbrales por docente y materia.

### Modified Capabilities
None

## Approach
Implement `Calificacion` and `UmbralMateria` tables. The `Calificacion` model will store `finalizado: Boolean` and `es_numerica: Boolean`. If a completion report is uploaded, it creates/updates grades with `finalizado=True`. Ungraded qualitative activities are easily detected where `finalizado=True`, `es_numerica=False`, and grades are NULL.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/calificacion.py` | New | Model `Calificacion` |
| `backend/app/models/umbral.py` | New | Model `UmbralMateria` |
| `backend/app/repositories/calificacion.py` | New | Repository for grades operations |
| `backend/app/repositories/umbral.py` | New | Repository for threshold settings |
| `backend/app/schemas/calificacion.py` | New | Pydantic validation schemas for grades |
| `backend/app/schemas/umbral.py` | New | Pydantic validation schemas for thresholds |
| `backend/app/services/calificacion_service.py` | New | Service logic for parsing, grading, and finalization cross-ref |
| `backend/app/api/v1/routers/calificaciones.py` | New | Endpoints for grades and umbral |
| `backend/alembic/versions/` | New | Alembic schema migrations |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Multi-tenant leakage | Low | Scoped repository queries extending `BaseRepository` |
| Unmatched emails | Medium | Hashing and batch lookup against `EntradaPadron.email_hash` |
| Unauthorized data clearing | Low | Restricting grade clearing strictly to `current_user.id` (RN-04) |

## Rollback Plan
Run `alembic downgrade` to drop the tables and rollback files using Git.

## Dependencies
- Completed `c-09-padron-ingesta-moodle`.

## Success Criteria
- [ ] Import grades from LMS CSV with column detection.
- [ ] Auto-calculates `aprobado` status according to custom or default thresholds.
- [ ] Completion reports update `finalizado` flag.
- [ ] Grade deletion is strictly isolated per teacher (RN-04).
- [ ] At least 80% line coverage and 90% business rule coverage.
