import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { equiposService } from '../services/equipos.service';
import type { EquipoClonarPayload } from '../types/coordinacion.types';

const emptyClonar: EquipoClonarPayload = {
  source_materia_id: '',
  source_cohorte_id: '',
  target_materia_id: '',
  target_cohorte_id: '',
  nuevo_desde: '',
};

export const EquiposPage = () => {
  const queryClient = useQueryClient();
  const [clonar, setClonar] = useState<EquipoClonarPayload>(emptyClonar);
  const [nuevaAsig, setNuevaAsig] = useState({
    usuario_id: '',
    rol_id: '',
    materia_id: '',
    cohorte_id: '',
    comisionesStr: '',
    desde: new Date().toISOString().split('T')[0],
    hasta: '',
  });
  const [feedback, setFeedback] = useState<string | null>(null);

  // Queries para la tabla y formularios
  const { data: equipos, isLoading, isError } = useQuery({
    queryKey: ['mis-equipos'],
    queryFn: equiposService.getMisEquipos,
  });

  const { data: usuarios } = useQuery({
    queryKey: ['admin-usuarios'],
    queryFn: equiposService.getUsuarios,
  });

  const { data: materias } = useQuery({
    queryKey: ['admin-materias'],
    queryFn: equiposService.getMaterias,
  });

  const { data: cohortes } = useQuery({
    queryKey: ['admin-cohortes'],
    queryFn: equiposService.getCohortes,
  });

  const { data: roles } = useQuery({
    queryKey: ['admin-roles'],
    queryFn: equiposService.getRoles,
  });

  // Mutaciones
  const clonarMutation = useMutation({
    mutationFn: () => equiposService.clonarEquipo(clonar),
    onSuccess: () => {
      setFeedback('Equipo clonado correctamente.');
      setClonar(emptyClonar);
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
    },
    onError: (err: unknown) => {
      const status = (err as { response?: { status?: number } })?.response?.status;
      setFeedback(status === 409 ? 'El destino ya tiene asignaciones activas.' : 'Error al clonar el equipo.');
    },
  });

  const crearAsigMutation = useMutation({
    mutationFn: () => {
      const comisiones = nuevaAsig.comisionesStr
        ? nuevaAsig.comisionesStr.split(',').map((c) => c.trim()).filter(Boolean)
        : [];
      return equiposService.crearAsignacion({
        usuario_id: nuevaAsig.usuario_id,
        rol_id: nuevaAsig.rol_id,
        materia_id: nuevaAsig.materia_id || null,
        cohorte_id: nuevaAsig.cohorte_id || null,
        comisiones: comisiones.length > 0 ? comisiones : null,
        desde: new Date(nuevaAsig.desde).toISOString(),
        hasta: nuevaAsig.hasta ? new Date(nuevaAsig.hasta).toISOString() : null,
      });
    },
    onSuccess: () => {
      setFeedback('Asignación/Comisión creada correctamente.');
      setNuevaAsig({
        usuario_id: '',
        rol_id: '',
        materia_id: '',
        cohorte_id: '',
        comisionesStr: '',
        desde: new Date().toISOString().split('T')[0],
        hasta: '',
      });
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
    },
    onError: () => {
      setFeedback('Error al crear la asignación/comisión.');
    },
  });

  const handleExport = async () => {
    const blob = await equiposService.exportarEquipo({});
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'equipo_docente.csv';
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Equipos Docentes</h1>
          <p className="text-slate-500 mt-1">Gestión de asignaciones académicas, creación de comisiones y exportación de datos.</p>
        </div>
        <button
          onClick={handleExport}
          className="inline-flex items-center px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 active:bg-indigo-800 shadow-sm transition-all duration-150"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Exportar CSV
        </button>
      </header>

      {feedback && (
        <div className="flex items-center justify-between rounded-xl border border-indigo-100 bg-indigo-50/50 px-4 py-3 text-sm text-indigo-800 animate-fade-in shadow-sm">
          <span>{feedback}</span>
          <button onClick={() => setFeedback(null)} className="text-indigo-500 hover:text-indigo-700 font-semibold">
            Cerrar
          </button>
        </div>
      )}

      {/* Grilla principal con Formularios y Tabla */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Panel de formularios (1/3 de ancho en pantallas grandes) */}
        <div className="lg:col-span-1 space-y-8">
          
          {/* Formulario 1: Nueva Asignación / Comisión */}
          <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center">
              <span className="w-1.5 h-6 bg-indigo-600 rounded mr-2.5 inline-block"></span>
              Nueva Comisión / Asignación
            </h2>
            
            <form
              onSubmit={(e) => {
                e.preventDefault();
                crearAsigMutation.mutate();
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Docente / Usuario</label>
                <select
                  required
                  value={nuevaAsig.usuario_id}
                  onChange={(e) => setNuevaAsig({ ...nuevaAsig, usuario_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Seleccionar Docente...</option>
                  {usuarios?.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.nombre} {u.apellidos} ({u.email})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Rol</label>
                <select
                  required
                  value={nuevaAsig.rol_id}
                  onChange={(e) => setNuevaAsig({ ...nuevaAsig, rol_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Seleccionar Rol...</option>
                  {roles?.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Materia</label>
                <select
                  value={nuevaAsig.materia_id}
                  onChange={(e) => setNuevaAsig({ ...nuevaAsig, materia_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Ninguna (Rol Global)</option>
                  {materias?.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nombre} ({m.codigo})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Cohorte</label>
                <select
                  value={nuevaAsig.cohorte_id}
                  onChange={(e) => setNuevaAsig({ ...nuevaAsig, cohorte_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Ninguna</option>
                  {cohortes?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Comisiones</label>
                <input
                  type="text"
                  placeholder="Ej: A, B (separadas por coma)"
                  value={nuevaAsig.comisionesStr}
                  onChange={(e) => setNuevaAsig({ ...nuevaAsig, comisionesStr: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Desde</label>
                  <input
                    required
                    type="date"
                    value={nuevaAsig.desde}
                    onChange={(e) => setNuevaAsig({ ...nuevaAsig, desde: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Hasta</label>
                  <input
                    type="date"
                    value={nuevaAsig.hasta}
                    onChange={(e) => setNuevaAsig({ ...nuevaAsig, hasta: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={crearAsigMutation.isPending}
                className="w-full mt-2 inline-flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 shadow-sm transition-all duration-150"
              >
                {crearAsigMutation.isPending ? 'Guardando...' : 'Crear Asignación'}
              </button>
            </form>
          </section>

          {/* Formulario 2: Clonar Equipo */}
          <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center">
              <span className="w-1.5 h-6 bg-slate-600 rounded mr-2.5 inline-block"></span>
              Clonar Equipo
            </h2>
            
            <form
              onSubmit={(e) => {
                e.preventDefault();
                clonarMutation.mutate();
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Materia Origen</label>
                <select
                  required
                  value={clonar.source_materia_id}
                  onChange={(e) => setClonar({ ...clonar, source_materia_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Seleccionar Materia...</option>
                  {materias?.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Cohorte Origen</label>
                <select
                  required
                  value={clonar.source_cohorte_id}
                  onChange={(e) => setClonar({ ...clonar, source_cohorte_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Seleccionar Cohorte...</option>
                  {cohortes?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Materia Destino</label>
                <select
                  required
                  value={clonar.target_materia_id}
                  onChange={(e) => setClonar({ ...clonar, target_materia_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Seleccionar Materia...</option>
                  {materias?.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Cohorte Destino</label>
                <select
                  required
                  value={clonar.target_cohorte_id}
                  onChange={(e) => setClonar({ ...clonar, target_cohorte_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white"
                >
                  <option value="">Seleccionar Cohorte...</option>
                  {cohortes?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Nuevo Inicio</label>
                <input
                  required
                  type="date"
                  value={clonar.nuevo_desde}
                  onChange={(e) => setClonar({ ...clonar, nuevo_desde: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={clonarMutation.isPending}
                className="w-full inline-flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-white bg-slate-700 rounded-xl hover:bg-slate-800 active:bg-slate-900 disabled:opacity-50 shadow-sm transition-all duration-150"
              >
                {clonarMutation.isPending ? 'Clonando...' : 'Clonar Equipo'}
              </button>
            </form>
          </section>

        </div>

        {/* Tabla de listado de equipos (2/3 de ancho en pantallas grandes) */}
        <div className="lg:col-span-2 space-y-4">
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">Listado de Asignaciones y Equipos</h2>
              <span className="bg-slate-100 text-slate-600 text-xs font-semibold px-2.5 py-1 rounded-full">
                {equipos ? `${equipos.length} registros` : '0 registros'}
              </span>
            </div>

            {isLoading && (
              <div className="p-8 text-center text-slate-500">
                <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                Cargando asignaciones...
              </div>
            )}
            
            {isError && (
              <div className="p-8 text-center text-red-500">
                Error al cargar el listado de asignaciones.
              </div>
            )}

            {equipos && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50/75">
                    <tr>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Usuario</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Rol</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Materia</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Cohorte</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Comisiones</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Vigencia</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {equipos.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-6 py-10 text-center text-sm text-slate-400">
                          No hay asignaciones de equipo vigentes.
                        </td>
                      </tr>
                    )}
                    {equipos.map((a) => (
                      <tr key={a.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 text-sm font-medium text-slate-900">
                          {a.usuario_nombre || a.usuario_id}
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-500">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">
                            {a.rol_nombre || a.rol_id}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-500">
                          {a.materia_nombre || a.materia_id || <span className="text-slate-400 font-light">—</span>}
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-500">
                          {a.cohorte_nombre || a.cohorte_id || <span className="text-slate-400 font-light">—</span>}
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-500">
                          {a.comisiones && a.comisiones.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {a.comisiones.map((c) => (
                                <span key={c} className="bg-indigo-50 text-indigo-700 text-xs font-semibold px-2 py-0.5 rounded">
                                  {c}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-400 font-light">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-500">
                          <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold leading-5 ${
                            a.estado_vigencia === 'Vigente' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {a.estado_vigencia}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>

      </div>
    </div>
  );
};
