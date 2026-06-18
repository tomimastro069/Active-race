import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comunicacionesService } from '../../academico-docente/services/comunicaciones.service';
import type { ComunicacionItem } from '../../academico-docente/services/comunicaciones.service';

interface Lote {
  loteId: string;
  asunto: string;
  total: number;
}

const agruparPorLote = (items: ComunicacionItem[]): Lote[] => {
  const mapa = new Map<string, Lote>();
  for (const item of items) {
    const loteId = item.lote_id ?? item.id;
    const actual = mapa.get(loteId);
    if (actual) {
      actual.total += 1;
    } else {
      mapa.set(loteId, { loteId, asunto: item.asunto, total: 1 });
    }
  }
  return Array.from(mapa.values());
};

export const AprobacionComunicacionesPage = () => {
  const queryClient = useQueryClient();

  const { data: comunicaciones, isLoading, isError } = useQuery({
    queryKey: ['comunicaciones-pendientes'],
    queryFn: () => comunicacionesService.listar('Pendiente'),
  });

  const lotes = useMemo(() => agruparPorLote(comunicaciones ?? []), [comunicaciones]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['comunicaciones-pendientes'] });

  const aprobarMut = useMutation({
    mutationFn: (loteId: string) => comunicacionesService.aprobarLote(loteId),
    onSuccess: invalidate,
  });
  const cancelarMut = useMutation({
    mutationFn: (loteId: string) => comunicacionesService.cancelarLote(loteId),
    onSuccess: invalidate,
  });

  const procesando = aprobarMut.isPending || cancelarMut.isPending;

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      <header className="border-b border-slate-100 pb-4">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Aprobación de Envíos</h1>
        <p className="text-slate-500 mt-1">Revisá y aprobá los lotes de correos pendientes antes del despacho.</p>
      </header>

      {isLoading && <div className="text-slate-500">Cargando cola...</div>}
      {isError && <div className="text-red-500">Error al cargar las comunicaciones.</div>}

      {comunicaciones && lotes.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-6 text-center text-slate-400">
          No hay envíos pendientes de aprobación.
        </div>
      )}

      <div className="space-y-3">
        {lotes.map((lote) => (
          <div key={lote.loteId} className="bg-white rounded-2xl border border-slate-200 p-5 flex items-center justify-between gap-4">
            <div>
              <p className="font-bold text-slate-900">{lote.asunto}</p>
              <p className="text-sm text-slate-500">{lote.total} destinatario(s) — Pendiente</p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                onClick={() => cancelarMut.mutate(lote.loteId)}
                disabled={procesando}
                className="px-4 py-2 text-sm font-semibold text-slate-700 border border-slate-300 rounded-xl hover:bg-slate-50 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => aprobarMut.mutate(lote.loteId)}
                disabled={procesando}
                className="px-4 py-2 text-sm font-semibold text-white bg-green-600 rounded-xl hover:bg-green-700 disabled:opacity-50"
              >
                Aprobar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
