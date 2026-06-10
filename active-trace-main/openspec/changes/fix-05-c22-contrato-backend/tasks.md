# Tasks: fix-05-c22-contrato-backend

## 1. Tipos y servicios

- [x] 1.1 Reescribir `types/academico.types.ts` con los shapes reales de los responses Pydantic.
- [x] 1.2 Reescribir `academico.service.ts` (umbral, preview/import/vaciar calificaciones,
      atrasados, ranking, monitor, tps-sin-corregir con flujo de dos pasos).
- [x] 1.3 Reescribir `comunicaciones.service.ts` (preview por template, enqueue con
      destinatarios, resumen de lote `por_estado`).

## 2. Componentes y páginas

- [x] 2.1 `TabAtrasados`: columnas actividad/motivo.
- [x] 2.2 `TabCalificaciones`: preview con `headers`/`estimated_grades_count`; resultado de
      import con `imported_count`/`unmatched_emails`.
- [x] 2.3 `TabComunicaciones`: destinatarios por email, preview renderizado único, tracking
      derivado de `por_estado`.
- [x] 2.4 `TabTrabajosSinCorregir`: columnas actividad/fecha de importación; export CSV.
- [x] 2.5 `ComisionDashboard`: `umbral_pct`; `setUmbral(materia_id, ...)`.
- [x] 2.6 `MonitorSeguimientoPage`: materia/cohorte obligatorios + filtros reales.

## 3. Tests y verificación

- [x] 3.1 Actualizar tests de servicios (paths/payloads reales) y de `ComisionDashboard`.
- [x] 3.2 `tsc --noEmit` limpio.
- [x] 3.3 Vitest en verde.
