import { api } from '../../../shared/services/api';

export interface Guardia {
  id: string;
  materia_id: string;
  asignacion_id: string;
  dia_semana: string;
  hora_inicio: string;
  hora_fin: string;
  estado: string;
  created_at: string;
  updated_at: string;
}

export const guardiasService = {
  listar: async (materiaId?: string) => {
    const params = materiaId ? { materia_id: materiaId } : undefined;
    const response = await api.get<Guardia[]>('/guardias/', { params });
    return response.data;
  },
};
