## Exploration: c-08-equipos-docentes

### Current State
El sistema ya cuenta con el modelo base `Asignacion` (E5) y un `AsignacionService` que resuelve operaciones elementales de CRUD (crear, modificar, listar, obtener, eliminar) sobre asignaciones individuales. Estas operaciones también están expuestas en un router básico `asignaciones.py` bajo `/api/v1/asignaciones`. Las operaciones actuales generan auditoría básica (`ASIGNACION_CREAR`, etc.), pero no existen flujos masivos de administración ni agrupaciones bajo el concepto de "equipo docente". 

### Affected Areas
- `backend/app/schemas/asignacion.py` — Requiere nuevos esquemas para las operaciones de negocio complejas: alta masiva (`AsignacionMasivaCreate`), clonación (`AsignacionClonar`), modificación masiva de vigencia (`AsignacionVigenciaUpdate`), y exportación.
- `backend/app/services/asignacion.py` (o nuevo servicio) — Necesitará lógica bulk-insert para evitar N+1 queries, operaciones transaccionales para clonado de equipos y validación de superposición de vigencias.
- `backend/app/api/v1/routers/asignaciones.py` (o nuevo router) — Exposición de los endpoints específicos para la gestión del equipo (masiva, clonar, exportar) y la vista "mis-equipos".

### Approaches
1. **Extender `AsignacionService` y `asignaciones.py`** — Agregar todas las funcionalidades (asignación masiva, clonado, vigencias, vistas mis-equipos) dentro de los mismos archivos existentes.
   - Pros: Menor cantidad de archivos, reuso directo de dependencias.
   - Cons: `AsignacionService` viola el Principio de Responsabilidad Única al mezclar CRUD atómico con flujos de dominio complejos (exportación, clonado masivo).
   - Effort: Low

2. **Crear capa de dominio dedicada: `EquiposService` y `equipos.py`** — Mantener `AsignacionService` para CRUD atómico, e implementar un nuevo servicio y router enfocados en el "Equipo Docente", consumiendo el repositorio de `Asignacion`.
   - Pros: Separa responsabilidades, el código queda alineado semánticamente con la épica (equipos docentes), facilita escalabilidad futura y mantiene legibilidad.
   - Cons: Requiere un nivel extra de coordinación de inyecciones (usar Repositories dentro del nuevo servicio).
   - Effort: Medium

### Recommendation
**Approach 2 (Crear capa dedicada `EquiposService`)**. El concepto de "Equipo Docente" es un agrupador de negocio superior a la simple "Asignación". Separar la gestión masiva, el clonado entre períodos y las exportaciones en un servicio específico previene que el CRUD base se convierta en un monolito inmanejable. Los endpoints deben exponerse idealmente en `/api/v1/equipos/*`.

### Risks
- **Rendimiento N+1**: Clonar un equipo docente con múltiples roles y comisiones o hacer alta masiva debe resolverse con `bulk_insert` u operaciones transaccionales eficientes.
- **Superposición temporal**: Al clonar o actualizar vigencia masivamente, se deben establecer controles para no generar colisiones ni pisar responsables existentes si el usuario se equivoca de fechas (RN-12).
- **Seguridad en Mis Equipos**: El endpoint `mis-equipos` debe obligatoriamente filtrar por `get_current_user()` y no depender de un ID pasado por URL, previniendo visualización de datos ajenos.

### Ready for Proposal
Yes — La arquitectura actual está lista y las áreas de impacto están perfectamente delimitadas. El orquestador puede continuar hacia la propuesta del change C-08.
