## Exploration: C-13 Encuentros y Guardias

### Current State
El proyecto tiene implementados los modelos base de la arquitectura multi-tenant (`Tenant`, `Usuario`, `Asignacion`, `Materia`, etc.) como parte de las fases previas (C-01 a C-07). Los componentes de infraestructura como base de datos, migraciones (Alembic) y middlewares de seguridad (RBAC) están funcionando. Actualmente no existe ninguna estructura de base de datos ni lógica de negocio para gestionar encuentros sincrónicos (slots y sus instancias) ni guardias de tutores. Las entidades `E9`, `E10` y `E11` definidas en la KB están completamente ausentes.

### Affected Areas
- `backend/app/models/encuentro.py` — [NEW] Definición de `SlotEncuentro` (E9) e `InstanciaEncuentro` (E10) heredando de `TimestampedTenant`.
- `backend/app/models/guardia.py` — [NEW] Definición de `Guardia` (E11) heredando de `TimestampedTenant`.
- `backend/app/schemas/encuentro.py` — [NEW] Validaciones Pydantic de entrada y salida para encuentros.
- `backend/app/schemas/guardia.py` — [NEW] Validaciones Pydantic para guardias.
- `backend/app/repositories/encuentro_repository.py` — [NEW] Consultas con scope de tenant para slots e instancias.
- `backend/app/repositories/guardia_repository.py` — [NEW] Consultas con scope de tenant para guardias.
- `backend/app/services/encuentro_service.py` — [NEW] Lógica de negocio (generación de recurrencias de instancias, vinculación slot-instancia).
- `backend/app/services/guardia_service.py` — [NEW] Lógica para registrar guardias (F6.6).
- `backend/app/api/routers/encuentros.py` — [NEW] Endpoints HTTP protegidos por `encuentros:gestionar`.
- `backend/app/api/routers/guardias.py` — [NEW] Endpoints HTTP para guardias.
- `backend/app/main.py` — [MODIFY] Registro de los nuevos routers.
- `backend/alembic/versions/` — [NEW] Archivo de migración de Alembic para crear las 3 tablas.

### Approaches
1. **Modelado Integrado (Un solo módulo para la Épica 6)** — Agrupar Slot, Instancia y Guardia en un solo archivo de modelo, repositorio y router (`encuentros_y_guardias.py`).
   - Pros: Menos archivos, todo lo relacionado a la Épica 6 queda en una misma ubicación.
   - Cons: Acopla funcionalidades distintas (clases sincrónicas vs guardias de tutoría) que crecerán a diferentes ritmos.
   - Effort: Low

2. **Modelado Separado por Entidad Lógica (Recomendado)** — Crear archivos separados para `encuentro` (incluye Slot e Instancia por su fuerte relación) y `guardia` en cada capa de Clean Architecture (models, schemas, repos, services, routers).
   - Pros: Alto nivel de cohesión, clara separación de responsabilidades, tests más enfocados y facilidad para futuros features (como métricas exclusivas de guardias).
   - Cons: Mayor cantidad de archivos iniciales.
   - Effort: Medium

### Recommendation
Se recomienda el **Approach 2 (Modelado Separado)**. Aunque ambos módulos pertenecen a la Épica 6, "Encuentros" (clases sincrónicas y sus grabaciones) y "Guardias" (horarios de disponibilidad) tienen reglas de negocio y flujos de usuario disjuntos. Separarlos respeta los lineamientos de Clean Architecture ya presentes en la base de código.

### Risks
- **Cálculo de Fechas en Recurrencias**: La función para crear encuentros recurrentes (F6.1) debe iterar correctamente sumando 7 días por cada semana indicada en `cant_semanas`, lo cual puede fallar con cambios de mes o años bisiestos si no se usan librerías estándar como `datetime` de forma segura.
- **Relaciones Opcionales**: Una `InstanciaEncuentro` puede o no tener un `slot_id` (encuentro único F6.2). Esto implica campos `nullable=True` en la Foreign Key que deben manejarse sin errores de integridad referencial.
- **Aislamiento Multi-Tenant**: Toda consulta nueva, especialmente las vistas globales de coordinación (F6.5), debe aplicar obligatoriamente el filtrado por `tenant_id`.

### Ready for Proposal
Yes — la exploración ha sido completada exitosamente. El usuario puede proceder a lanzar el proposal utilizando `/opsx:propose C-13-encuentros-y-guardias` (o `/sdd-propose C-13-encuentros-y-guardias`).
