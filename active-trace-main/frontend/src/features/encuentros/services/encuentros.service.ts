import { api } from '../../../shared/services/api';
import type {
  InstanciaEncuentro,
  MateriaSimple,
  SlotRecurrentePayload,
  EncuentroUnicoPayload,
  InstanciaUpdatePayload,
} from '../types/encuentros.types';

export const encuentrosService = {
  getMaterias: async () => {
    const response = await api.get<MateriaSimple[]>('/admin/materias');
    return response.data;
  },

  listarPorMateria: async (materiaId: string) => {
    const response = await api.get<InstanciaEncuentro[]>(`/encuentros/materias/${materiaId}`);
    return response.data;
  },

  crearRecurrente: async (payload: SlotRecurrentePayload) => {
    const response = await api.post('/encuentros/recurrentes', payload);
    return response.data;
  },

  crearUnico: async (payload: EncuentroUnicoPayload) => {
    const response = await api.post<InstanciaEncuentro>('/encuentros/unicos', payload);
    return response.data;
  },

  actualizarInstancia: async (instanciaId: string, payload: InstanciaUpdatePayload) => {
    const response = await api.patch<InstanciaEncuentro>(`/encuentros/instancias/${instanciaId}`, payload);
    return response.data;
  },

  getCronograma: async (materiaId: string) => {
    const response = await api.get<string>(`/encuentros/exportar/${materiaId}`, { responseType: 'text' });
    return response.data;
  },
};
