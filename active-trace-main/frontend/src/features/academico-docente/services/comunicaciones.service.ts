import { api } from '../../../shared/services/api';

// Contrato real del backend (app/schemas/comunicacion.py)

export interface Destinatario {
  email: string;
  nombre: string;
  actividades_faltantes: string;
}

export interface ComunicacionPreviewRequest {
  asunto_template: string;
  cuerpo_template: string;
  variables: Record<string, string>;
}

export interface ComunicacionPreview {
  asunto_renderizado: string;
  cuerpo_renderizado: string;
}

export interface ComunicacionEnviarRequest {
  asunto_template: string;
  cuerpo_template: string;
  destinatarios: Destinatario[];
  materia_id: string;
}

export interface ComunicacionItem {
  id: string;
  tenant_id: string;
  enviado_por: string;
  materia_id: string;
  destinatario_hash: string;
  asunto: string;
  cuerpo: string;
  estado: string;
  lote_id: string | null;
  aprobado: boolean;
  enviado_at: string | null;
  intentos: number;
  max_intentos: number;
}

// Estados del dominio (RN-15): claves de por_estado
export type EstadoComunicacion = 'Pendiente' | 'Enviando' | 'Enviado' | 'Error' | 'Cancelado';

export interface LoteResumen {
  lote_id: string;
  total: number;
  por_estado: Partial<Record<EstadoComunicacion, number>>;
}

export const comunicacionesService = {
  // Preview obligatorio (F3.1, RN-16): renderiza los templates con variables de muestra.
  previewMensaje: async (payload: ComunicacionPreviewRequest) => {
    const response = await api.post<ComunicacionPreview>('/comunicaciones/preview', payload);
    return response.data;
  },

  // Encola el lote (F3.2). Devuelve una Comunicacion por destinatario, todas con el mismo lote_id.
  enviarLote: async (payload: ComunicacionEnviarRequest) => {
    const response = await api.post<ComunicacionItem[]>('/comunicaciones/', payload);
    return response.data;
  },

  getLoteStatus: async (loteId: string) => {
    const response = await api.get<LoteResumen>(`/comunicaciones/lotes/${loteId}`);
    return response.data;
  },

  // Cola de aprobación (F3.3, HU-12): lista comunicaciones, opcionalmente por estado.
  listar: async (estado?: EstadoComunicacion) => {
    const params = estado ? { estado } : undefined;
    const response = await api.get<ComunicacionItem[]>('/comunicaciones/', { params });
    return response.data;
  },

  // Aprobar un lote completo: pasa de Pendiente a Enviando (RN-17).
  aprobarLote: async (loteId: string) => {
    const response = await api.post(`/comunicaciones/lotes/${loteId}/aprobar`, {});
    return response.data;
  },

  // Cancelar un lote completo: pasa a Cancelado (RN-17).
  cancelarLote: async (loteId: string) => {
    const response = await api.post(`/comunicaciones/lotes/${loteId}/cancelar`, {});
    return response.data;
  },
};
