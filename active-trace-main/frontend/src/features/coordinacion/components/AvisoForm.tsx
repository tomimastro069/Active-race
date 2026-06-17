import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { avisosService } from '../services/avisos.service';
import type { AlcanceAviso, AvisoCreatePayload } from '../types/coordinacion.types';

const ALCANCES: AlcanceAviso[] = ['Global', 'PorMateria', 'PorCohorte', 'PorRol'];
const SEVERIDADES = ['info', 'warning', 'critical'];

const emptyAviso: AvisoCreatePayload = {
  alcance: 'Global',
  severidad: 'info',
  titulo: '',
  cuerpo: '',
  inicio_en: '',
  fin_en: '',
  orden: 0,
  requiere_ack: false,
};

export const AvisoForm = () => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<AvisoCreatePayload>(emptyAviso);
  const [showPreview, setShowPreview] = useState(false);

  const mutation = useMutation({
    mutationFn: () => avisosService.crearAviso(form),
    onSuccess: () => {
      setForm(emptyAviso);
      setShowPreview(false);
      queryClient.invalidateQueries({ queryKey: ['avisos-activos'] });
    },
  });

  const handlePreviewSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowPreview(true);
  };

  const handleConfirmSend = () => {
    mutation.mutate();
  };

  return (
    <>
      <form
        onSubmit={handlePreviewSubmit}
        className="space-y-3 rounded-lg border border-slate-200 p-4 bg-white"
      >
        <h3 className="text-base font-semibold text-slate-800">Redactar Aviso Institucional</h3>

        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm text-slate-600">
            Alcance
            <select
              value={form.alcance}
              onChange={(e) => setForm({ ...form, alcance: e.target.value as AlcanceAviso })}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            >
              {ALCANCES.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </label>
          <label className="text-sm text-slate-600">
            Severidad
            <select
              value={form.severidad}
              onChange={(e) => setForm({ ...form, severidad: e.target.value })}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            >
              {SEVERIDADES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>

        {form.alcance === 'PorMateria' && (
          <input required placeholder="ID de la Materia" value={form.materia_id ?? ''}
            onChange={(e) => setForm({ ...form, materia_id: e.target.value })}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
        )}
        {form.alcance === 'PorCohorte' && (
          <input required placeholder="ID de la Cohorte" value={form.cohorte_id ?? ''}
            onChange={(e) => setForm({ ...form, cohorte_id: e.target.value })}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
        )}
        {form.alcance === 'PorRol' && (
          <input required placeholder="Rol destino (ej. PROFESOR)" value={form.rol_destino ?? ''}
            onChange={(e) => setForm({ ...form, rol_destino: e.target.value })}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
        )}

        <input required placeholder="Título del aviso" value={form.titulo}
          onChange={(e) => setForm({ ...form, titulo: e.target.value })}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm font-medium" />
        <textarea required placeholder="Escribí el cuerpo del comunicado acá..." value={form.cuerpo}
          onChange={(e) => setForm({ ...form, cuerpo: e.target.value })}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm" rows={4} />

        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm text-slate-600">
            Inicio Vigencia
            <input required type="datetime-local" value={form.inicio_en}
              onChange={(e) => setForm({ ...form, inicio_en: e.target.value })}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" />
          </label>
          <label className="text-sm text-slate-600">
            Fin Vigencia
            <input required type="datetime-local" value={form.fin_en}
              onChange={(e) => setForm({ ...form, fin_en: e.target.value })}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" />
          </label>
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" checked={form.requiere_ack}
            onChange={(e) => setForm({ ...form, requiere_ack: e.target.checked })} />
          Solicitar Acuse de Recibo obligatorio a los destinatarios
        </label>

        <button
          type="submit"
          className="w-full rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
        >
          Vista Previa y Enviar
        </button>
        {mutation.isError && <p className="text-sm text-red-500">Error al publicar el aviso.</p>}
      </form>

      {/* Modal de Preview Obligatorio */}
      {showPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col">
            <div className="bg-slate-100 p-4 border-b border-slate-200 flex justify-between items-center">
              <h4 className="font-semibold text-slate-800">Vista Previa del Aviso</h4>
              <button onClick={() => setShowPreview(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>
            
            {/* Mock de Bandeja de Entrada */}
            <div className="p-6 bg-slate-50 flex-grow">
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold">
                    AT
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Active Trace</p>
                    <p className="text-xs text-slate-500">Para: Todos ({form.alcance})</p>
                  </div>
                </div>
                
                <h1 className="text-xl font-bold text-slate-900 mb-4">{form.titulo}</h1>
                <div className="prose prose-sm text-slate-700 whitespace-pre-wrap">
                  {form.cuerpo}
                </div>
                
                {form.requiere_ack && (
                  <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-md">
                    <p className="text-sm text-amber-800 text-center font-medium">
                      Este comunicado requiere acuse de recibo.
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-slate-200 flex justify-end space-x-3 bg-white">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
              >
                Seguir Editando
              </button>
              <button
                onClick={handleConfirmSend}
                disabled={mutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Enviando...' : 'Confirmar y Enviar Aviso'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
