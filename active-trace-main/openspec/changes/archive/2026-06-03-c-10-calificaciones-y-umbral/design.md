# Design: c-10-calificaciones-y-umbral

## Technical Approach
Siguiendo Clean Architecture, introduciremos las capas de persistencia y lógica para Calificaciones y Umbrales de Aprobación.
Se crearán los modelos de SQLAlchemy `Calificacion` y `UmbralMateria`.
El servicio `CalificacionService` encapsulará el procesamiento y validación del archivo CSV de calificaciones y del reporte de finalización. La lógica de negocio cruzará el padrón activo (usando `VersionPadron` y `EntradaPadron`) para asociar a los alumnos mediante su email hash, y evaluará si el alumno aprobó la actividad según el umbral configurado para la materia (usando `UmbralMateria` del docente asignado, o el valor por defecto de 60%).

## Architecture Decisions

### Decision: Simplificación de Entregas con finalizado y es_numerica en Calificacion
**Choice**: Agregar los atributos `finalizado` (Boolean) y `es_numerica` (Boolean) en el modelo `Calificacion`.
**Alternatives considered**: Tabla intermedia `finalizacion_actividad`.
**Rationale**: Redundancia mínima. Evita JOINs costosos y la sincronización compleja. Almacenar directamente si la actividad está finalizada y si es numérica en la misma fila permite resolver las RN-07 y RN-08 con filtros SQL directos e indexados sobre una única tabla.

### Decision: Aislamiento estricto de Vaciado por Docente (RN-04)
**Choice**: El método de borrado/vaciado en `CalificacionRepository` filtrará obligatoriamente por `actor_id` (del docente logueado) y `materia_id`.
**Alternatives considered**: Permitir que coordinación o admin pasen un docente a borrar.
**Rationale**: Garantiza por diseño el cumplimiento de la RN-04, aislando por completo la operación de vaciado al scope del usuario logueado en la materia actual, sin poder afectar registros de otros docentes.

## Data Flow

```text
       LMS Grades CSV / Completion CSV
                     │
                     ▼
             [CalificacionesRouter]
                     │
         (Preview: parses CSV, returns cols)
         (Import: parses CSV, matches active EntradaPadron.email_hash)
                     │
                     ▼
            [CalificacionService] ◄─── [UmbralMateria] (Evaluation)
                     │
                     ▼
            [CalificacionRepository]
                     │
            (Tx: Bulk Insert/Upsert)
                     │
                     ▼
                [PostgreSQL]
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/calificacion.py` | Create | Modelo SQLAlchemy para `Calificacion` (E7). |
| `backend/app/models/umbral.py` | Create | Modelo SQLAlchemy para `UmbralMateria` (E8). |
| `backend/app/repositories/calificacion.py` | Create | Operaciones de DB de calificaciones (bulk insert, isolated clear, pending grades). |
| `backend/app/repositories/umbral.py` | Create | Operaciones de DB para umbrales. |
| `backend/app/schemas/calificacion.py` | Create | Esquemas Pydantic para preview, import y respuestas de calificaciones. |
| `backend/app/schemas/umbral.py` | Create | Esquemas Pydantic para configuración y respuesta del umbral. |
| `backend/app/services/calificacion_service.py` | Create | Lógica de parseo CSV, evaluación de notas contra umbrales y cruce con finalizaciones. |
| `backend/app/api/v1/routers/calificaciones.py` | Create | Endpoints para preview, import, finalización, vaciar y gestión de umbral. |
| `backend/app/main.py` | Modify | Registrar el router de calificaciones. |
| `backend/alembic/versions/` | Create | Script de migración de Alembic para crear las tablas correspondientes. |

## Interfaces / Contracts

### SQLAlchemy Models
```python
class UmbralMateria(Base, TimestampedTenant):
    __tablename__ = 'umbral_materia'
    
    asignacion_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey('asignacion.id', ondelete='CASCADE'), nullable=False)
    materia_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey('materias.id', ondelete='CASCADE'), nullable=False)
    umbral_pct = Column(Integer, default=60, nullable=False)
    valores_aprobatorios = Column(JSON, nullable=True) # e.g. ["Satisfactorio", "Supera lo esperado"]

class Calificacion(Base, TimestampedTenant):
    __tablename__ = 'calificacion'
    
    entrada_padron_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey('entrada_padron.id', ondelete='CASCADE'), nullable=False)
    materia_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey('materias.id', ondelete='CASCADE'), nullable=False)
    actividad = Column(String(255), nullable=False)
    nota_numerica = Column(Float, nullable=True)
    nota_textual = Column(String(100), nullable=True)
    aprobado = Column(Boolean, nullable=False, default=False)
    finalizado = Column(Boolean, nullable=False, default=True)
    es_numerica = Column(Boolean, nullable=False, default=True)
    origen = Column(String(50), nullable=False, default="Importado") # Importado | Manual
    importado_at = Column(DateTime, nullable=True)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Derivación de `aprobado` | Probar lógica de cálculo con nota numérica vs. umbral y cualitativas vs. catálogo aprobatorio. |
| Integration | Aislamiento y versionado | Validar que el vaciado solo elimine registros del `actor_id` y que queries hereden tenant scoping. |
| E2E | Ciclo completo de importación | Carga de CSV de notas y posterior cruce con CSV de finalización mediante endpoints API. |

## Migration / Rollout
Se generará una migración estándar de Alembic. No requiere migración de datos ya que son tablas nuevas.
