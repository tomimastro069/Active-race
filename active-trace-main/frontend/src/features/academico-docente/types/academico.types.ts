// Tipos transcritos de los schemas Pydantic reales del backend
// (app/schemas/analisis.py, app/schemas/calificacion.py, app/schemas/umbral.py).

export interface CommissionContextType {
  materiaId: string;
  cohorteId: string;
  umbralPct: number;
  setUmbralPct: (val: number) => void;
}

// GET /analisis/atrasados -> AlumnoAtrasadoResponse
export interface AlumnoAtrasado {
  padron_id: string;
  nombre: string;
  apellido: string;
  actividad: string;
  motivo: string;
}

// GET /analisis/ranking -> RankingResponse
export interface RankingItem {
  padron_id: string;
  nombre: string;
  apellido: string;
  actividades_aprobadas: number;
}

// GET/POST /calificaciones/umbral -> UmbralMateriaResponse
export interface ConfiguracionUmbral {
  umbral_pct: number;
  valores_aprobatorios?: string[] | null;
}

// POST /calificaciones/preview-csv -> CalificacionPreviewResponse
export interface PreviewCalificaciones {
  headers: string[];
  rows: Record<string, unknown>[];
  estimated_grades_count: number;
}

// POST /calificaciones/import-csv -> CalificacionImportResponse
export interface ImportResultado {
  imported_count: number;
  unmatched_emails: string[];
}

// GET /analisis/monitor -> MonitorResponse (una fila por alumno x actividad)
export interface MonitorItem {
  padron_id: string;
  nombre: string;
  apellido: string;
  actividad: string;
  estado: string;
  nota?: number | string | null;
  importado_at?: string | null;
}

// GET /analisis/tps-sin-corregir -> TPSinCorregirResponse
export interface EntregaPendiente {
  padron_id: string;
  nombre: string;
  apellido: string;
  actividad: string;
  importado_at?: string | null;
}
