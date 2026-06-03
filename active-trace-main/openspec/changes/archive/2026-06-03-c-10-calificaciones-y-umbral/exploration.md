## Exploration: c-10-calificaciones-y-umbral

### Current State
El sistema cuenta con la base de datos multi-tenant, autenticación, RBAC y auditoría (C-01 a C-05). Asimismo, posee la estructura académica (C-06), usuarios y asignaciones (C-07), y la ingesta de padrón Moodle/CSV (C-09) recientemente implementada e integrada en el archivo de cambios.
Actualmente, el sistema carece de la gestión y almacenamiento de notas/calificaciones, del cálculo de aprobación y del soporte para umbrales de aprobación configurables por docente y materia. Tampoco existen las tablas correspondientes a `calificacion` y `umbral_materia`.

### Affected Areas
- `backend/app/models/calificacion.py` (NUEVO) — Define el modelo `Calificacion` (E7).
- `backend/app/models/umbral.py` (NUEVO) — Define el modelo `UmbralMateria` (E8).
- `backend/app/repositories/calificacion.py` (NUEVO) — Repositorio para transacciones de calificaciones (importar, vaciar, etc.).
- `backend/app/repositories/umbral.py` (NUEVO) — Repositorio para gestionar umbrales.
- `backend/app/schemas/calificacion.py` (NUEVO) — Esquemas Pydantic para importar, previsualizar y reportar calificaciones.
- `backend/app/schemas/umbral.py` (NUEVO) — Esquemas Pydantic para configurar umbrales.
- `backend/app/services/calificacion_service.py` (NUEVO) — Lógica de negocio para importar calificaciones, parsear CSV de notas y reportes de finalización, cruzar datos y aplicar umbrales de aprobación.
- `backend/app/api/v1/routers/calificaciones.py` (NUEVO) — Router de FastAPI para la API de calificaciones y configuración de umbrales.
- `backend/alembic/versions/` (NUEVO) — Migración para crear las tablas `calificacion` y `umbral_materia`.
- `backend/tests/` (NUEVO) — Tests automáticos de repository, service y API endpoints en modo Strict TDD.

### Approaches

1. **Persistencia Simplificada en Calificacion (Recomendado)**  
   Agregar columnas `finalizado` y `es_numerica` en el modelo `Calificacion`.
   - **Cómo funciona**:
     - Al importar calificaciones, se crea `Calificacion` con `finalizado = True` (puesto que tiene nota, la actividad fue completada).
     - Si la columna de nota termina en `(Real)`, se setea `es_numerica = True`. De lo contrario, `es_numerica = False`.
     - Al importar el reporte de finalización, si el alumno tiene la actividad completada pero no existe registro de nota, se crea un registro en `Calificacion` con `finalizado = True`, `es_numerica = False` (para actividades cualitativas) y notas en `None`.
     - Las entregas sin corregir se obtienen filtrando: `finalizado == True`, `nota_numerica == None`, `nota_textual == None` y `es_numerica == False`.
   - **Pros**: 
     - Diseño extremadamente limpio, sin necesidad de crear una tabla intermedia de finalización de actividades.
     - Consultas rápidas y sencillas con filtros directos sobre una única tabla.
     - Cumple con RN-07 y RN-08 a la perfección.
   - **Cons**: 
     - Se asume por defecto que las entregas sin nota importadas del reporte de finalización son cualitativas (escala textual) a menos que se cruce con columnas numéricas, lo cual se alinea perfectamente con la RN-08.
   - **Effort**: Medium

2. **Esquema de Tablas Separadas**  
   Crear una tabla independiente `finalizacion_actividad` para registrar el estado de entrega del alumno por actividad y cruzarla mediante JOINs con `calificacion` en tiempo de consulta.
   - **Cómo funciona**:
     - `FinalizacionActividad` almacena la relación `entrada_padron_id`, `actividad`, `finalizado` (Boolean).
     - El cruce se hace mediante un query con OUTER JOIN entre `finalizacion_actividad` y `calificacion` filtrando aquellas finalizaciones sin nota.
   - **Pros**:
     - Separación física de conceptos (entrega vs. calificación).
   - **Cons**:
     - Incrementa la complejidad del esquema de base de datos con tablas adicionales.
     - Mayor overhead de JOINs y lógica de sincronización (upsert doble).
   - **Effort**: High

### Recommendation
Se recomienda la **Opción 1: Persistencia Simplificada en Calificacion**. Aporta una excelente velocidad de desarrollo, menor complejidad en JOINs y encaja idealmente con las reglas de negocio especificadas (RN-07 y RN-08), reduciendo la sobrecarga de código en FastAPI y SQLAlchemy.

### Risks
- **Detección de Escalas Textuales**: Asegurar que cualquier nota que no sea numérica (sin `(Real)`) sea validada contra el catálogo de valores aprobatorios en `UmbralMateria` (por defecto `["Satisfactorio", "Supera lo esperado"]`).
- **Aislamiento por Docente (RN-04)**: El borrado o vaciado de calificaciones de una materia debe ser estrictamente aislado al docente que ejecuta la acción (usuario_id x materia_id), previniendo que afecte las calificaciones cargadas por otros docentes.
- **Cruce de Padrón**: Si un email en el CSV de calificaciones no coincide exactamente con el email_hash del padrón activo, el registro debe ser reportado o ignorado para evitar inconsistencias.

### Ready for Proposal
Yes — La especificación técnica está alineada con los requisitos y lista para proceder con el diseño técnico y la propuesta formal.
