import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useCommission } from '../pages/ComisionDashboard';
import { comunicacionesService } from '../services/comunicaciones.service';
import type { ComunicacionPreview, Destinatario } from '../services/comunicaciones.service';

const parseDestinatarios = (raw: string): Destinatario[] =>
  raw
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .map(email => ({
      email,
      nombre: email.split('@')[0],
      actividades_faltantes: '',
    }));

export const TabComunicaciones = () => {
  const { materiaId } = useCommission();
  const [emails, setEmails] = useState<string>(''); // separados por coma
  const [asunto, setAsunto] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [previewData, setPreviewData] = useState<ComunicacionPreview | null>(null);
  const [activeLoteId, setActiveLoteId] = useState<string | null>(null);

  const previewMutation = useMutation({
    mutationFn: () => {
      const destinatarios = parseDestinatarios(emails);
      const muestra = destinatarios[0];
      return comunicacionesService.previewMensaje({
        asunto_template: asunto,
        cuerpo_template: mensaje,
        variables: muestra
          ? { nombre: muestra.nombre, actividades_faltantes: muestra.actividades_faltantes }
          : {},
      });
    },
    onSuccess: (data) => setPreviewData(data),
  });

  const enviarMutation = useMutation({
    mutationFn: () => comunicacionesService.enviarLote({
      asunto_template: asunto,
      cuerpo_template: mensaje,
      destinatarios: parseDestinatarios(emails),
      materia_id: materiaId,
    }),
    onSuccess: (comunicaciones) => {
      setActiveLoteId(comunicaciones[0]?.lote_id ?? null);
      setPreviewData(null);
      setAsunto('');
      setMensaje('');
      setEmails('');
    }
  });

  // Polling del lote activo mientras queden envíos en curso
  const { data: lote } = useQuery({
    queryKey: ['loteStatus', activeLoteId],
    queryFn: () => comunicacionesService.getLoteStatus(activeLoteId!),
    enabled: !!activeLoteId,
    refetchInterval: (query) => {
      const porEstado = query.state.data?.por_estado;
      if (!porEstado) return 5000;
      const enCurso = (porEstado.Pendiente ?? 0) + (porEstado.Enviando ?? 0);
      return enCurso > 0 ? 5000 : false;
    },
  });

  const enviados = lote?.por_estado.Enviado ?? 0;
  const fallidos = lote?.por_estado.Error ?? 0;
  const enCurso = (lote?.por_estado.Pendiente ?? 0) + (lote?.por_estado.Enviando ?? 0);
  const total = lote?.total ?? 0;
  const estadoLote = enCurso > 0 ? 'EN PROCESO' : fallidos > 0 ? 'CON ERRORES' : 'COMPLETADO';

  return (
    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
      {/* Formulario de envío */}
      <section className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-800">Nueva Comunicación</h3>

        <div>
          <label className="block text-sm font-medium text-slate-700">Emails de alumnos (separados por coma)</label>
          <input
            type="text"
            value={emails}
            onChange={e => setEmails(e.target.value)}
            placeholder="Ej: ana@mail.com, juan@mail.com"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Asunto</label>
          <input
            type="text"
            value={asunto}
            onChange={e => setAsunto(e.target.value)}
            placeholder="Aviso de tareas faltantes"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Mensaje Template</label>
          <textarea
            value={mensaje}
            onChange={e => setMensaje(e.target.value)}
            rows={4}
            placeholder="Hola {{nombre}}, notamos que tienes actividades pendientes."
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
          />
          <p className="mt-1 text-xs text-slate-500">Variables disponibles: {`{{nombre}}, {{actividades_faltantes}}`}</p>
        </div>

        <button
          onClick={() => previewMutation.mutate()}
          disabled={!emails || !asunto || !mensaje || previewMutation.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded shadow hover:bg-indigo-700 disabled:opacity-50"
        >
          {previewMutation.isPending ? 'Cargando...' : 'Previsualizar'}
        </button>
      </section>

      {/* Previsualización y Tracking */}
      <section className="bg-slate-50 p-6 rounded-lg border border-slate-200">
        {previewData && (
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-800">Previsualización (con datos del primer destinatario)</h4>
            <div className="bg-white p-3 rounded shadow-sm border border-slate-100 text-sm">
              <p className="text-slate-600 font-medium border-b pb-1 mb-1">{previewData.asunto_renderizado}</p>
              <p className="text-slate-600 whitespace-pre-wrap">{previewData.cuerpo_renderizado}</p>
            </div>
            <button
              onClick={() => enviarMutation.mutate()}
              disabled={enviarMutation.isPending}
              className="w-full bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700 disabled:opacity-50"
            >
              Confirmar y Enviar Lote
            </button>
          </div>
        )}

        {lote && (
          <div className="mt-6 border-t border-slate-200 pt-6">
            <h4 className="font-semibold text-slate-800 mb-4">Estado del Lote de Envío</h4>
            <div className="bg-white p-4 rounded shadow-sm border border-slate-100">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-500">ID Lote:</span>
                <span className="text-sm font-mono">{lote.lote_id.split('-')[0]}...</span>
              </div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-medium text-slate-500">Estado:</span>
                <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5
                  ${estadoLote === 'COMPLETADO' ? 'bg-green-100 text-green-800' :
                    estadoLote === 'CON ERRORES' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800 animate-pulse'}`}>
                  {estadoLote}
                </span>
              </div>

              {/* Progress bar */}
              <div className="relative pt-1">
                <div className="flex mb-2 items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-indigo-600 bg-indigo-200">
                      Progreso
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-indigo-600">
                      {total > 0 ? Math.round(((enviados + fallidos) / total) * 100) : 0}%
                    </span>
                  </div>
                </div>
                <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-indigo-200">
                  <div style={{ width: `${total > 0 ? (enviados / total) * 100 : 0}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-green-500"></div>
                  <div style={{ width: `${total > 0 ? (fallidos / total) * 100 : 0}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-red-500"></div>
                </div>
                <p className="text-xs text-center text-slate-500">
                  {enviados} enviados, {fallidos} con error de {total} total
                </p>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};
