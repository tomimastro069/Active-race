# Proposal: C-08 Equipos Docentes

## Intent

Implementar la gestión masiva y contextual de Equipos Docentes (Épica 4), permitiendo asignaciones en bloque, clonación de equipos entre períodos y administración masiva de vigencias. Se busca eliminar el cuello de botella del CRUD individual por docente en el setup de cada cuatrimestre.

## Scope

### In Scope
- Endpoint para asignación masiva de docentes a un equipo.
- Endpoint transaccional para clonar un equipo completo hacia una nueva cohorte/período.
- Endpoint para actualización masiva de vigencias de todo un equipo.
- Endpoint para exportar equipo docente.
- Vista `mis-equipos` filtrada estrictamente por el usuario autenticado.
- Creación de `EquiposService` (servicio de dominio) y router específico `/api/v1/equipos`.

### Out of Scope
- Interfaz gráfica en el Frontend (delegado a C-23).
- CRUD atómico y administración individual de asignaciones (ya existente en `AsignacionService`).

## Capabilities

### New Capabilities
- `equipos-gestion-masiva`: Asignación masiva, clonación transaccional y actualización de vigencias en bloque.
- `equipos-exportacion`: Exportación del listado de asignaciones de un equipo a archivo.
- `equipos-vista-docente`: Endpoint específico para que el docente vea sus propios equipos sin comprometer datos ajenos.

### Modified Capabilities
- `user-academic-assignment-e5`: Ninguno (el esquema y requisitos subyacentes se mantienen, solo se añade lógica bulk superior).

## Approach

Crear un servicio de dominio especializado (`EquiposService`) que opere sobre el `AsignacionRepository` para manejar la lógica bulk (bulk inserts, validación transaccional de superposición de fechas al clonar). Esto mantiene el Principio de Responsabilidad Única al no inflar `AsignacionService`. Se creará un router `/api/v1/equipos` protegido por el guard `equipos:asignar` (para administración) y sin restricción extra (más allá del usuario activo) para `mis-equipos`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/schemas/asignacion.py` | Modified | Nuevos esquemas: `AsignacionMasivaCreate`, `AsignacionClonar`, `AsignacionVigenciaUpdate`. |
| `backend/app/services/equipos.py` | New | Lógica transaccional para asignación masiva, clonado y mis-equipos. |
| `backend/app/api/v1/routers/equipos.py` | New | Endpoints REST (`/api/v1/equipos/*`) para operaciones grupales. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| N+1 Queries al clonar o asignar en masa | Medium | Uso explícito de `insert().values()` masivo de SQLAlchemy dentro de una transacción. |
| Solapamiento de vigencias al clonar | Medium | Validar que el equipo destino no contenga asignaciones activas antes del clonado. |
| Fuga de datos en `mis-equipos` | High | Hardcodear `get_current_user().id` como filtro forzoso en la consulta; no aceptar ID por parámetro. |

## Rollback Plan

Dado que no hay cambios estructurales al modelo (E5 `Asignacion` queda intacto), basta con revertir el PR (git revert) para remover los endpoints y el servicio. Los registros creados erróneamente en bloque se pueden soft-deletear rastreando la auditoría masiva generada.

## Dependencies

- Requiere el modelo y repositorio base de `Asignacion` (C-07) completados.

## Success Criteria

- [ ] Un coordinador puede clonar el equipo de una cohorte a otra en una sola request (< 1 segundo).
- [ ] La operación masiva emite correctamente registros de auditoría identificables.
- [ ] El endpoint `mis-equipos` retorna exclusivamente registros correspondientes al docente que hace la petición.
