import { useQuery } from '@tanstack/react-query';
import { useCommission } from '../pages/ComisionDashboard';
import { academicoService } from '../services/academico.service';

export const TabAtrasados = () => {
  const { materiaId, cohorteId } = useCommission();

  const { data: atrasados, isLoading, isError } = useQuery({
    queryKey: ['atrasados', materiaId, cohorteId],
    queryFn: () => academicoService.getAtrasados(materiaId, cohorteId),
  });

  if (isLoading) return <div className="p-6 text-slate-500">Cargando alumnos atrasados...</div>;
  if (isError) return <div className="p-6 text-red-500">Error al cargar datos.</div>;

  return (
    <div className="p-6">
      <h3 className="text-lg font-semibold mb-4 text-slate-800">Alumnos Atrasados / En Riesgo</h3>
      
      {atrasados && atrasados.length > 0 ? (
        <div className="overflow-x-auto shadow ring-1 ring-black ring-opacity-5 rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900">Padrón</th>
                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Alumno</th>
                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Actividad</th>
                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Motivo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {atrasados.map((alumno, idx) => (
                <tr key={`${alumno.padron_id}-${alumno.actividad}-${idx}`} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-gray-900">{alumno.padron_id}</td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm font-medium text-gray-900">
                    {alumno.apellido}, {alumno.nombre}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{alumno.actividad}</td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm">
                    <span className="inline-flex rounded-full bg-red-100 px-2 text-xs font-semibold leading-5 text-red-800">
                      {alumno.motivo}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-slate-500">No se detectaron alumnos atrasados con el umbral actual.</p>
        </div>
      )}
    </div>
  );
};
