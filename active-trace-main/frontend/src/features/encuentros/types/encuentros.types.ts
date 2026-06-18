export type DiaSemana = 'Lunes' | 'Martes' | 'Miércoles' | 'Jueves' | 'Viernes' | 'Sábado' | 'Domingo';
export const DIAS_SEMANA: DiaSemana[] = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

export type EstadoEncuentro = 'Programado' | 'Realizado' | 'Suspendido';
export const ESTADOS_ENCUENTRO: EstadoEncuentro[] = ['Programado', 'Realizado', 'Suspendido'];

export interface MateriaSimple {
  id: string;
  codigo: string;
  nombre: string;
}

export interface InstanciaEncuentro {
  id: string;
  slot_id?: string | null;
  materia_id: string;
  titulo: string;
  fecha_hora: string;
  estado: EstadoEncuentro;
  meet_url?: string | null;
  video_url?: string | null;
  comentario?: string | null;
}

export interface SlotRecurrentePayload {
  materia_id: string;
  titulo: string;
  hora: string;
  dia_semana: DiaSemana;
  fecha_inicio: string;
  cant_semanas: number;
  meet_url: string;
}

export interface EncuentroUnicoPayload {
  materia_id: string;
  titulo: string;
  fecha_hora: string;
  meet_url?: string | null;
}

export interface InstanciaUpdatePayload {
  estado?: EstadoEncuentro;
  meet_url?: string | null;
  video_url?: string | null;
  comentario?: string | null;
}
