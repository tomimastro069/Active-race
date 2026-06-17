import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { equiposService } from '../../coordinacion/services/equipos.service';

export const ComisionesListPage = () => {
  const { data: asignaciones, isLoading, isError } = useQuery({
    queryKey: ['mis-equipos'],
    queryFn: equiposService.getMisEquipos,
  });

  // Deduplicar por materia + cohorte (una comisión = una materia en un cohorte)
  const comisiones = asignaciones
    ? Array.from(
        new Map(
          asignaciones
            .filter((a) => a.materia_id && a.cohorte_id)
            .map((a) => [`${a.materia_id}-${a.cohorte_id}`, a])
        ).values()
      )
    : [];

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Mis Comisiones</h1>
        <p className="text-slate-500 mt-1">
          Seleccioná una comisión para ver calificaciones, alumnos atrasados y trabajos sin corregir.
        </p>
      </header>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-36 rounded-xl bg-slate-100 animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-700">
          Error al cargar tus comisiones. Verificá que tu usuario tenga asignaciones activas.
        </div>
      )}

      {!isLoading && comisiones.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-4xl mb-4">📚</p>
          <p className="text-slate-600 font-medium">No tenés comisiones asignadas aún.</p>
          <p className="text-slate-400 text-sm mt-1">
            Un Coordinador o Administrador debe asignarte a una materia/cohorte.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {comisiones.map((a) => (
          <Link
            key={`${a.materia_id}-${a.cohorte_id}`}
            to={`/comisiones/${a.materia_id}/${a.cohorte_id}`}
            className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all duration-200"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center group-hover:bg-indigo-600 transition-colors">
                <svg className="w-5 h-5 text-indigo-600 group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                a.estado_vigencia === 'Activo' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'
              }`}>
                {a.estado_vigencia}
              </span>
            </div>

            <h2 className="font-semibold text-slate-800 group-hover:text-indigo-700 transition-colors line-clamp-1">
              {a.materia_nombre || a.materia_id}
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Cohorte: {a.cohorte_nombre || a.cohorte_id}
            </p>
            {a.rol_nombre && (
              <p className="text-xs text-indigo-500 mt-3 font-medium">{a.rol_nombre}</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
};
