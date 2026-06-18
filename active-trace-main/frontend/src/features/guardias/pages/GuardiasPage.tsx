import { useQuery } from '@tanstack/react-query';
import { guardiasService } from '../services/guardias.service';
import type { Guardia } from '../services/guardias.service';

const exportarCsv = (guardias: Guardia[]) => {
  const headers = ['Materia', 'Día', 'Hora inicio', 'Hora fin', 'Estado', 'Registrada'];
  const filas = guardias.map((g) => [
    g.materia_id, g.dia_semana, g.hora_inicio, g.hora_fin, g.estado, new Date(g.created_at).toLocaleDateString(),
  ]);
  const csv = [headers, ...filas].map((f) => f.join(';')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'mis-guardias.csv';
  a.click();
  URL.revokeObjectURL(url);
};

export const GuardiasPage = () => {
  const { data: guardias, isLoading, isError } = useQuery({
    queryKey: ['mis-guardias'],
    queryFn: () => guardiasService.listar(),
  });

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      <header className="border-b border-slate-100 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Mis Guardias</h1>
          <p className="text-slate-500 mt-1">Historial de tu disponibilidad registrada.</p>
        </div>
        <button
          onClick={() => guardias && exportarCsv(guardias)}
          disabled={!guardias || guardias.length === 0}
          className="px-4 py-2 text-sm font-semibold text-white bg-slate-700 rounded-xl hover:bg-slate-800 disabled:opacity-50"
        >
          Exportar CSV
        </button>
      </header>

      {isLoading && <div className="text-slate-500">Cargando guardias...</div>}
      {isError && <div className="text-red-500">Error al cargar las guardias.</div>}

      {guardias && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50/75">
              <tr>
                {['Materia', 'Día', 'Horario', 'Estado', 'Registrada'].map((h) => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {guardias.length === 0 && (
                <tr><td colSpan={5} className="px-5 py-10 text-center text-slate-400">No tenés guardias registradas.</td></tr>
              )}
              {guardias.map((g) => (
                <tr key={g.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3 text-slate-700">{g.materia_id}</td>
                  <td className="px-5 py-3 text-slate-700">{g.dia_semana}</td>
                  <td className="px-5 py-3 text-slate-700">{g.hora_inicio} – {g.hora_fin}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      g.estado === 'Aprobada' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'
                    }`}>{g.estado}</span>
                  </td>
                  <td className="px-5 py-3 text-slate-500">{new Date(g.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
