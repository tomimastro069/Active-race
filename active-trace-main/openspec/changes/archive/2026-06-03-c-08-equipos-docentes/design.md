# Design: C-08 Equipos Docentes

## Technical Approach
La funcionalidad se orquestará mediante un nuevo servicio de dominio `EquiposService` (`backend/app/services/equipos.py`), delegando la persistencia real a la tabla subyacente de `Asignacion`. Se expondrán las rutas necesarias en un nuevo archivo `backend/app/api/v1/routers/equipos.py`. Las operaciones de asignación y clonación se construirán utilizando consultas bulk asíncronas de SQLAlchemy (`insert().values(...)`) envueltas en la misma transacción de la request, de forma que si falla la validación de un usuario, todo el bloque se cancele por seguridad de los datos.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|----------|--------|-------------------------|-----------|
| Servicio dedicado | `EquiposService` y router `/equipos` | Añadir lógica al `AsignacionService` existente | El modelo de permisos permite desacoplar los dominios fácilmente. La administración en masa amerita su propio flujo sin inflar el CRUD elemental. |
| Mecanismo de inserción | `insert(Asignacion).values(...)` | `session.add_all([Asignacion(...)])` | Mayor control sobre el rendimiento bajo el motor asyncpg para cargas iniciales de cientos de profesores a la vez. |
| Seguridad en "Mis equipos" | Omitir param. `usuario_id` en el schema | Pasar el ID por la URL e interceptarlo | Al no existir en la interfaz del Endpoint, se anula por diseño la vulnerabilidad IDOR (Insecure Direct Object Reference). |

## Data Flow

    Router (/api/v1/equipos) ─── Payload ──→ EquiposService
               │                                   │
    get_current_user (Auth)                 Validaciones + Bulk
               │                                   │
               └───────── AuditLog ◄─────── AsignacionRepository (SQLAlchemy 2.0)

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/schemas/equipos.py` | Create | DTOs para clonado, modificación masiva y exportación. |
| `backend/app/services/equipos.py` | Create | Lógica transaccional de dominio (mass assign, mass update, clone). |
| `backend/app/api/v1/routers/equipos.py` | Create | Endpoints protegidos mediante el dependency `require_permission("equipos:asignar")`. |
| `backend/app/main.py` | Modify | Inclusión y ruteo del nuevo `router` de equipos. |

## Interfaces / Contracts

```python
class AsignacionMasivaCreate(BaseModel):
    usuario_ids: List[UUID]
    rol_id: UUID
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comisiones: Optional[List[str]] = None
    responsable_id: Optional[UUID] = None
    desde: datetime
    hasta: Optional[datetime] = None

class EquipoClonarRequest(BaseModel):
    source_materia_id: UUID
    source_cohorte_id: UUID
    target_materia_id: UUID
    target_cohorte_id: UUID
    nuevo_desde: datetime
    nuevo_hasta: Optional[datetime] = None
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Validaciones (solapamientos temporales, usuarios inválidos) | Testing del Service inyectando el mock del `AsignacionRepository` |
| Integration | Comportamiento del bulk insert en DB real | Uso de `pytest-asyncio` con base de datos de test, asegurando inserción completa |
| E2E | Filtros de usuario activo (`mis-equipos`) y guards de seguridad | Httpx `AsyncClient` logueado con múltiples tokens simulando IDOR y éxito propio |

## Migration / Rollout

No migration required. El esquema de base de datos no cambia; los modelos transaccionales se asientan directamente sobre las tablas de asignación existentes.

## Open Questions

- None
