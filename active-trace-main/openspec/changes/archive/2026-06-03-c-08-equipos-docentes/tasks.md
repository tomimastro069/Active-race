# Tasks: C-08 Equipos Docentes

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~300 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Toda la épica 4 (Backend) | PR 1 | Base aislada en `/api/v1/equipos` y `EquiposService`. Tamaño seguro para un solo PR. |

## Phase 1: Foundation (Schemas)

- [x] 1.1 `backend/app/schemas/asignacion.py`: Agregar el DTO `AsignacionMasivaCreate`.
- [x] 1.2 `backend/app/schemas/asignacion.py`: Agregar el DTO `EquipoClonarRequest`.
- [x] 1.3 `backend/app/schemas/asignacion.py`: Agregar el DTO `AsignacionVigenciaUpdate`.

## Phase 2: Core Implementation (Service)

- [x] 2.1 `backend/app/services/equipos.py`: Crear `EquiposService` inyectando `AsignacionRepository`, `UsuarioRepository`, `RolRepository` y `AuditService`.
- [x] 2.2 `backend/app/services/equipos.py`: Implementar `asignacion_masiva()` realizando inserción bulk dentro de la transacción.
- [x] 2.3 `backend/app/services/equipos.py`: Implementar `clonar_equipo()` asegurando que el contexto destino esté libre antes de clonar.
- [x] 2.4 `backend/app/services/equipos.py`: Implementar `modificar_vigencia_masiva()`.
- [x] 2.5 `backend/app/services/equipos.py`: Implementar `obtener_mis_equipos(usuario_id: UUID)`.
- [x] 2.6 `backend/app/services/equipos.py`: Implementar `exportar_equipo()` para retornar un listado enriquecido de las asignaciones de un contexto.

## Phase 3: Integration (Routers)

- [x] 3.1 `backend/app/api/v1/routers/equipos.py`: Crear router `/equipos` con guard `require_permission("equipos:asignar")` a nivel router.
- [x] 3.2 `backend/app/api/v1/routers/equipos.py`: `POST /api/v1/equipos/masiva` delegando a `asignacion_masiva`.
- [x] 3.3 `backend/app/api/v1/routers/equipos.py`: `POST /api/v1/equipos/clonar` delegando a `clonar_equipo`.
- [x] 3.4 `backend/app/api/v1/routers/equipos.py`: `PATCH /api/v1/equipos/vigencia` delegando a `modificar_vigencia_masiva`.
- [x] 3.5 `backend/app/api/v1/routers/equipos.py`: `GET /api/v1/equipos/exportar` delegando a `exportar_equipo`.
- [x] 3.6 `backend/app/api/v1/routers/equipos.py`: `GET /api/v1/equipos/mis-equipos` excluyendo el guard anterior y forzando `current_user.id`.
- [x] 3.7 `backend/app/main.py`: Registrar el nuevo `router_equipos`.

## Phase 4: Testing

- [x] 4.1 `backend/tests/services/test_equipos.py`: Unit test sobre `clonar_equipo` validando el rechazo por solapamiento.
- [x] 4.2 `backend/tests/services/test_equipos.py`: Unit test validando la inserción bulk exitosa con auditoría.
- [x] 4.3 `backend/tests/api/test_equipos.py`: E2E sobre `/api/v1/equipos/mis-equipos` forzando otro JWT para asegurar que retorna solo data del usuario activo.
