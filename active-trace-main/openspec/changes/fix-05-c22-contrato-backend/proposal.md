# Fix 05 — C-22 (frontend académico-docente) consume un contrato que no existe en el backend

## Why

Los servicios de la feature `academico-docente` fueron escritos contra un contrato inventado:
paths, formas de request y formas de response no coinciden con el backend real (C-10/C-11/C-12).
Sus tests pasan porque mockean el cliente HTTP. En uso real, prácticamente toda la feature
devuelve 404/422:

| Frontend llamaba | Backend real |
|---|---|
| `GET /calificaciones/comision/{m}/{c}/umbral` | `GET /calificaciones/umbral?materia_id=` (por materia, no por cohorte) |
| `POST /calificaciones/comision/{m}/{c}/umbral` `{umbral_aprobacion}` | `POST /calificaciones/umbral` `{materia_id, umbral_pct}` |
| `POST /calificaciones/comision/{m}/{c}/preview` | `POST /calificaciones/preview-csv` (multipart, solo `file`) |
| `POST /calificaciones/comision/{m}/{c}/import` (+`actividades`) | `POST /calificaciones/import-csv` (Form: `materia_id`, `cohorte_id`, `file`) |
| `DELETE /calificaciones/comision/{m}/{c}` | `POST /calificaciones/vaciar` `{materia_id, cohorte_id}` |
| `GET /analisis/atrasados/{m}/{c}` (path) | `GET /analisis/atrasados?materia_id=&cohorte_id=` (query) |
| `GET /analisis/ranking/{m}/{c}` | `GET /analisis/ranking?...` |
| `POST /analisis/sin-corregir/{m}/{c}` (file) | `POST /calificaciones/import-completion-csv` + `GET /analisis/tps-sin-corregir?...` |
| `GET /analisis/monitor` (sin materia) | `GET /analisis/monitor?materia_id=&cohorte_id=&...` (obligatorios) |
| `POST /comunicaciones/preview/{m}/{c}` `{alumnos_ids,...}` → lista | `POST /comunicaciones/preview` `{asunto_template, cuerpo_template, variables}` → un render |
| `POST /comunicaciones/lote/{m}/{c}` → `{batch_id}` | `POST /comunicaciones/` `{asunto_template, cuerpo_template, destinatarios[], materia_id}` → `ComunicacionResponse[]` con `lote_id` |
| `GET /comunicaciones/lote/{id}` `{estado, enviados, fallidos, total}` | `GET /comunicaciones/lotes/{id}` → `{lote_id, total, por_estado}` |

Los tipos también divergen (p. ej. `AlumnoAtrasado` real es `{padron_id, nombre, apellido,
actividad, motivo}`; el monitor devuelve filas por actividad, no porcentaje de cumplimiento).

## What Changes

- `types/academico.types.ts`: tipos transcritos de los schemas Pydantic reales
  (`AlumnoAtrasadoResponse`, `RankingResponse`, `CalificacionPreviewResponse`,
  `CalificacionImportResponse`, `UmbralMateriaResponse`, `MonitorResponse`,
  `TPSinCorregirResponse`).
- `academico.service.ts` y `comunicaciones.service.ts`: paths, métodos y payloads reales.
  "Detectar trabajos sin corregir" se implementa con el flujo real de dos pasos
  (`import-completion-csv` → `tps-sin-corregir`). El estado del lote expone `por_estado`
  con los valores del dominio (`Pendiente/Enviando/Enviado/Error/Cancelado`).
- Componentes/páginas adaptados a las formas reales: `TabAtrasados` (actividad/motivo),
  `TabCalificaciones` (`headers` + `estimated_grades_count`, import sin selección de
  actividades — el backend no la soporta, gap ya reportado de C-10), `TabComunicaciones`
  (template + destinatarios por email, tracking derivado de `por_estado`),
  `TabTrabajosSinCorregir` (actividad/importado_at), `ComisionDashboard` (`umbral_pct`),
  `MonitorSeguimientoPage` (materia y cohorte obligatorios, filas por actividad).
- Tests de servicios y página actualizados al contrato real.

## Impact

- Solo `frontend/src/features/academico-docente/**` (servicios, tipos, componentes, páginas,
  tests). Sin cambios de backend.
- `tsc --noEmit` limpio y Vitest en verde.
- Gap que queda documentado (no es parte de este fix): el backend no implementa selección de
  actividades en el import (F1.1) ni un monitor transversal sin materia (F2.7).
