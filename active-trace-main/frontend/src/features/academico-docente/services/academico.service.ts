import { api } from '../../../shared/services/api';
import type {
  AlumnoAtrasado,
  RankingItem,
  ConfiguracionUmbral,
  PreviewCalificaciones,
  ImportResultado,
  MonitorItem,
  EntregaPendiente,
} from '../types/academico.types';

export interface MonitorFiltros {
  regional?: string;
  comision?: string;
  search?: string;
  estado_actividad?: string;
}

export const academicoService = {
  // Configuración de Umbral (por materia, RN-03)
  getUmbral: async (materiaId: string) => {
    const response = await api.get<ConfiguracionUmbral | null>('/calificaciones/umbral', {
      params: { materia_id: materiaId },
    });
    return response.data;
  },

  setUmbral: async (materiaId: string, umbralPct: number) => {
    const response = await api.post<ConfiguracionUmbral>('/calificaciones/umbral', {
      materia_id: materiaId,
      umbral_pct: umbralPct,
    });
    return response.data;
  },

  // Importación de notas (F1.1)
  previewCalificaciones: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<PreviewCalificaciones>('/calificaciones/preview-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  importarCalificaciones: async (materiaId: string, cohorteId: string, file: File) => {
    const formData = new FormData();
    formData.append('materia_id', materiaId);
    formData.append('cohorte_id', cohorteId);
    formData.append('file', file);
    const response = await api.post<ImportResultado>('/calificaciones/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  vaciarCalificaciones: async (materiaId: string, cohorteId: string) => {
    const response = await api.post('/calificaciones/vaciar', {
      materia_id: materiaId,
      cohorte_id: cohorteId,
    });
    return response.data;
  },

  // Análisis y Reportes (F2.2, F2.3)
  getAtrasados: async (materiaId: string, cohorteId: string) => {
    const response = await api.get<AlumnoAtrasado[]>('/analisis/atrasados', {
      params: { materia_id: materiaId, cohorte_id: cohorteId },
    });
    return response.data;
  },

  getRanking: async (materiaId: string, cohorteId: string) => {
    const response = await api.get<RankingItem[]>('/analisis/ranking', {
      params: { materia_id: materiaId, cohorte_id: cohorteId },
    });
    return response.data;
  },

  // Monitor (F2.7/F2.8) — materia y cohorte son obligatorios en el backend
  getMonitor: async (materiaId: string, cohorteId: string, filtros?: MonitorFiltros) => {
    const response = await api.get<MonitorItem[]>('/analisis/monitor', {
      params: { materia_id: materiaId, cohorte_id: cohorteId, ...filtros },
    });
    return response.data;
  },

  // Detección de entregas sin corregir (F1.2 + F2.6): el flujo real es de dos pasos —
  // importar el reporte de finalización del LMS y consultar los TPs entregados sin nota.
  detectarTrabajosSinCorregir: async (materiaId: string, cohorteId: string, file: File) => {
    const formData = new FormData();
    formData.append('materia_id', materiaId);
    formData.append('cohorte_id', cohorteId);
    formData.append('file', file);
    await api.post('/calificaciones/import-completion-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    const response = await api.get<EntregaPendiente[]>('/analisis/tps-sin-corregir', {
      params: { materia_id: materiaId, cohorte_id: cohorteId },
    });
    return response.data;
  }
};
