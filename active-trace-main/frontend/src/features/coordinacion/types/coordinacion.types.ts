// --- Equipos (C-08) ---

export interface Asignacion {
  id: string;
  tenant_id: string;
  usuario_id: string;
  rol_id: string;
  materia_id?: string | null;
  carrera_id?: string | null;
  cohorte_id?: string | null;
  comisiones?: string[] | null;
  responsable_id?: string | null;
  desde: string;
  hasta?: string | null;
  estado_vigencia: string;
  created_at: string;
  updated_at: string;
  usuario_nombre?: string | null;
  rol_nombre?: string | null;
  materia_nombre?: string | null;
  cohorte_nombre?: string | null;
}

export interface AsignacionMasivaPayload {
  usuario_ids: string[];
  rol_id: string;
  materia_id?: string | null;
  carrera_id?: string | null;
  cohorte_id?: string | null;
  comisiones?: string[] | null;
  responsable_id?: string | null;
  desde: string;
  hasta?: string | null;
}

export interface EquipoClonarPayload {
  source_materia_id: string;
  source_cohorte_id: string;
  target_materia_id: string;
  target_cohorte_id: string;
  nuevo_desde: string;
  nuevo_hasta?: string | null;
}

export interface AsignacionVigenciaPayload {
  materia_id?: string | null;
  carrera_id?: string | null;
  cohorte_id?: string | null;
  desde?: string | null;
  hasta?: string | null;
}

// --- Avisos (C-15) ---

export type AlcanceAviso = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol';

export interface Aviso {
  id: string;
  tenant_id: string;
  alcance: AlcanceAviso;
  materia_id?: string | null;
  cohorte_id?: string | null;
  rol_destino?: string | null;
  severidad: string;
  titulo: string;
  cuerpo: string;
  inicio_en: string;
  fin_en: string;
  orden: number;
  activo: boolean;
  requiere_ack: boolean;
  created_at: string;
}

export interface AvisoCreatePayload {
  alcance: AlcanceAviso;
  materia_id?: string | null;
  cohorte_id?: string | null;
  rol_destino?: string | null;
  severidad: string;
  titulo: string;
  cuerpo: string;
  inicio_en: string;
  fin_en: string;
  orden?: number;
  activo?: boolean;
  requiere_ack?: boolean;
}

// --- Tareas (C-16) ---

export type EstadoTarea = 'Pendiente' | 'En progreso' | 'Resuelta' | 'Cancelada';

export const ESTADOS_TAREA: EstadoTarea[] = ['Pendiente', 'En progreso', 'Resuelta', 'Cancelada'];

export interface Tarea {
  id: string;
  descripcion: string;
  materia_id?: string | null;
  contexto_id?: string | null;
  asignado_a: string;
  asignado_por: string;
  estado: EstadoTarea;
  created_at: string;
  updated_at: string;
}

export interface TareaCreatePayload {
  descripcion: string;
  asignado_a: string;
  materia_id?: string | null;
  contexto_id?: string | null;
}

export interface ComentarioTarea {
  id: string;
  tarea_id: string;
  autor_id: string;
  texto: string;
  created_at: string;
  updated_at: string;
}

// --- Monitor transversal (C-11) ---

export interface MonitorItem {
  padron_id: string;
  nombre: string;
  apellido: string;
  actividad: string;
  estado: string;
  nota?: number | string | null;
  importado_at?: string | null;
}

export interface MonitorFiltros {
  materia_id: string;
  cohorte_id: string;
  regional?: string;
  comision?: string;
  search?: string;
  estado_actividad?: string;
  desde_fecha?: string;
  hasta_fecha?: string;
}

// --- Tipos de Estructura Académica y Roles ---

export interface UsuarioSimple {
  id: string;
  nombre: string;
  apellidos: string;
  email: string;
}

export interface MateriaSimple {
  id: string;
  codigo: string;
  nombre: string;
}

export interface CohorteSimple {
  id: string;
  nombre: string;
  anio: number;
}

export interface RolSimple {
  id: string;
  nombre: string;
  descripcion?: string | null;
}

export interface AsignacionCreatePayload {
  usuario_id: string;
  rol_id: string;
  materia_id?: string | null;
  carrera_id?: string | null;
  cohorte_id?: string | null;
  comisiones?: string[] | null;
  responsable_id?: string | null;
  desde: string;
  hasta?: string | null;
}
