import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { avisosService } from '../../coordinacion/services/avisos.service';

export const AvisosBandejaPage = () => {
  const queryClient = useQueryClient();

  const { data: avisos, isLoading } = useQuery({
    queryKey: ['avisos-activos'],
    queryFn: avisosService.getActivos,
  });

  const ackMutation = useMutation({
    mutationFn: (avisoId: string) => avisosService.acusarRecibo(avisoId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['avisos-activos'] }),
  });

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      <header className="border-b border-slate-100 pb-4">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Avisos</h1>
        <p className="text-slate-500 mt-1">Novedades vigentes de la institución.</p>
      </header>

      {isLoading && <div className="text-slate-500">Cargando avisos...</div>}
      {avisos && avisos.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-6 text-center text-slate-400">
          No hay avisos vigentes.
        </div>
      )}

      <div className="space-y-4">
        {avisos?.map((aviso) => (
          <article key={aviso.id} className="bg-white rounded-2xl border border-slate-200 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-bold text-slate-900">{aviso.titulo}</h2>
                <p className="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{aviso.cuerpo}</p>
              </div>
              <span className="shrink-0 inline-flex rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
                {aviso.severidad}
              </span>
            </div>
            {aviso.requiere_ack && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => ackMutation.mutate(aviso.id)}
                  disabled={ackMutation.isPending}
                  className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:opacity-50"
                >
                  Acusar recibo
                </button>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
};
