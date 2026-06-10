import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { academicoService } from '../services/academico.service';

export const MonitorSeguimientoPage = () => {
  // El backend exige materia y cohorte (F2.8); los filtros son opcionales.
  const [materiaId, setMateriaId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [search, setSearch] = useState('');
  const [estadoActividad, setEstadoActividad] = useState('');

  const { data: monitorItems, isLoading, isError } = useQuery({
    queryKey: ['monitor', materiaId, cohorteId, search, estadoActividad],
    queryFn: () => academicoService.getMonitor(materiaId, cohorteId, {
      search: search || undefined,
      estado_actividad: estadoActividad || undefined,
    }),
    enabled: !!materiaId && !!cohorteId,
  });

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-900 mb-6">Monitor de Seguimiento</h1>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 mb-6 flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-slate-700">Materia (ID)</label>
          <input
            type="text"
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
            className="mt-1 block rounded-md border-gray-300 shadow-sm border p-2 text-sm"
            placeholder="UUID de la materia"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Cohorte (ID)</label>
          <input
            type="text"
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            className="mt-1 block rounded-md border-gray-300 shadow-sm border p-2 text-sm"
            placeholder="UUID de la cohorte"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Buscar (Nombre/Padrón)</label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mt-1 block rounded-md border-gray-300 shadow-sm border p-2 text-sm"
            placeholder="Ej: Pérez"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Estado de Actividad</label>
          <select
            value={estadoActividad}
            onChange={(e) => setEstadoActividad(e.target.value)}
            className="mt-1 block rounded-md border-gray-300 shadow-sm border p-2 text-sm w-40 bg-white"
          >
            <option value="">Cualquiera</option>
            <option value="Aprobado">Aprobado</option>
            <option value="Desaprobado">Desaprobado</option>
            <option value="Pendiente">Pendiente</option>
          </select>
        </div>
      </div>

      {/* Resultados */}
      {!materiaId || !cohorteId ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200 text-slate-500">
          Ingrese materia y cohorte para consultar el monitor.
        </div>
      ) : isLoading ? (
        <div className="text-slate-500">Cargando datos del monitor...</div>
      ) : isError ? (
        <div className="text-red-500">Error al cargar datos del monitor.</div>
      ) : monitorItems && monitorItems.length > 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alumno</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Padrón</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actividad</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nota</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Importado</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {monitorItems.map((item, idx) => (
                <tr key={`${item.padron_id}-${item.actividad}-${idx}`} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.apellido}, {item.nombre}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.padron_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.actividad}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${
                      item.estado === 'Aprobado' ? 'bg-green-100 text-green-800' :
                      item.estado === 'Desaprobado' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {item.estado}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.nota ?? '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.importado_at ? new Date(item.importado_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200 text-slate-500">
          No se encontraron registros con los filtros seleccionados.
        </div>
      )}
    </div>
  );
};
