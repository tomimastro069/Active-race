# Proposal: C-13 Encuentros y Guardias

## Intent

Habilitar la planificación, registro y seguimiento de clases sincrónicas (encuentros) y horarios de disponibilidad para tutorías (guardias). Esto permitirá a profesores organizar eventos recurrentes o únicos y a coordinadores monitorear su cumplimiento, aportando estructura al acompañamiento del estudiante.

## Scope

### In Scope
- Creación de encuentros recurrentes (Slot) y generación automática de instancias (InstanciaEncuentro).
- Creación de encuentros únicos.
- Edición de estado, links de meet y grabaciones de las instancias.
- Exportación de encuentros (fragmento HTML) para el aula virtual.
- Registro y listado de guardias para tutorías, con exportación.
- API endpoints protegidos por el permiso `encuentros:gestionar`.

### Out of Scope
- Interfaz gráfica frontend (pertenece a fases posteriores C-23).
- Integración automatizada directa por API con el LMS (solo se genera HTML).
- Módulos de coloquios o exámenes formales (C-14).

## Capabilities

### New Capabilities
- `encuentros-gestion`: Gestión de clases sincrónicas, creación recurrente/única, registro de grabaciones y generación de bloques HTML.
- `guardias-gestion`: Registro, listado y exportación de disponibilidades para guardias de tutores.

### Modified Capabilities
None

## Approach

Siguiendo el "Approach 2" (Modelado Separado) validado en la exploración, se implementarán dos dominios separados en backend (models, schemas, repos, services, routers): uno para `Encuentros` (Slot e Instancia) y otro para `Guardias`. Ambos heredarán de `TimestampedTenant`. La generación de encuentros recurrentes delegará el cálculo de fechas al servicio correspondiente, asegurando aislamiento tenant en todas las consultas mediante repositorios base.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/encuentro.py` | New | Modelos SlotEncuentro e InstanciaEncuentro |
| `backend/app/models/guardia.py` | New | Modelo Guardia |
| `backend/app/schemas/` | New | Schemas Pydantic para ambas entidades |
| `backend/app/repositories/` | New | Repositorios con filtro tenant implícito |
| `backend/app/services/` | New | Lógica de recurrencia y registro |
| `backend/app/api/routers/` | New | Endpoints de API |
| `backend/app/main.py` | Modified | Inclusión de routers |
| `backend/alembic/versions/` | New | Script de migración DB |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cálculo de recurrencias erróneo | Med | Pruebas unitarias exhaustivas con fechas límite (bisiestos, fin de mes). |
| Fuga de datos entre tenants | Med | Uso de Repositories base (`generic-repository-tenant-scoped`). |
| Inconsistencia Slot/Instancia | Low | Reglas estrictas en FK `slot_id` (nullable solo en encuentros únicos). |

## Rollback Plan

1. Revertir el PR o commit de la feature C-13.
2. Ejecutar downgrade de Alembic de la migración que crea las tablas `SlotEncuentro`, `InstanciaEncuentro` y `Guardia`.

## Dependencies

- C-07 Usuarios y Asignaciones (Completado en FASE 3).

## Success Criteria

- [ ] Un docente puede crear un encuentro recurrente de N semanas y se generan N instancias correctas.
- [ ] Un docente puede registrar una grabación en una instancia.
- [ ] Un tutor puede registrar una guardia.
- [ ] Todas las operaciones están restringidas por `encuentros:gestionar`.
