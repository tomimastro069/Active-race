import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { encuentrosService } from '../services/encuentros.service';
import { DIAS_SEMANA, ESTADOS_ENCUENTRO } from '../types/encuentros.types';
import type { InstanciaEncuentro } from '../types/encuentros.types';

export const EncuentrosPage = () => {
  const queryClient = useQueryClient();
  const [materiaId, setMateriaId] = useState('');
  const [recurrente, setRecurrente] = useState({
    titulo: '', hora: '18:00', dia_semana: 'Lunes', fecha_inicio: '', cant_semanas: 12, meet_url: '',
  });
  const [unico, setUnico] = useState({ titulo: '', fecha_hora: '', meet_url: '' });

  const { data: materias } = useQuery({ queryKey: ['materias'], queryFn: encuentrosService.getMaterias });
  const { data: instancias } = useQuery({
    queryKey: ['encuentros', materiaId],
    queryFn: () => encuentrosService.listarPorMateria(materiaId),
    enabled: !!materiaId,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['encuentros', materiaId] });

  const recurrenteMut = useMutation({
    mutationFn: () => encuentrosService.crearRecurrente({ materia_id: materiaId, ...recurrente, dia_semana: recurrente.dia_semana as never }),
    onSuccess: invalidate,
  });
  const unicoMut = useMutation({
    mutationFn: () => encuentrosService.crearUnico({ materia_id: materiaId, ...unico }),
    onSuccess: invalidate,
  });
  const updateMut = useMutation({
    mutationFn: (vars: { id: string; estado: string; video_url: string; comentario: string }) =>
      encuentrosService.actualizarInstancia(vars.id, { estado: vars.estado as never, video_url: vars.video_url, comentario: vars.comentario }),
    onSuccess: invalidate,
  });

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <header className="border-b border-slate-100 pb-4">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Encuentros</h1>
        <p className="text-slate-500 mt-1">Programá encuentros recurrentes o únicos y registrá lo ocurrido.</p>
      </header>

      <select value={materiaId} onChange={(e) => setMateriaId(e.target.value)} className="rounded-xl border border-slate-300 px-3.5 py-2 text-sm">
        <option value="">Seleccioná una materia</option>
        {materias?.map((m) => <option key={m.id} value={m.id}>{m.codigo} — {m.nombre}</option>)}
      </select>

      {materiaId && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <form onSubmit={(e) => { e.preventDefault(); recurrenteMut.mutate(); }} className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
            <h2 className="font-bold text-slate-800">Encuentro recurrente</h2>
            <input required placeholder="Título" value={recurrente.titulo} onChange={(e) => setRecurrente({ ...recurrente, titulo: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <div className="grid grid-cols-2 gap-2">
              <select value={recurrente.dia_semana} onChange={(e) => setRecurrente({ ...recurrente, dia_semana: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm">
                {DIAS_SEMANA.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
              <input type="time" value={recurrente.hora} onChange={(e) => setRecurrente({ ...recurrente, hora: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
              <input required type="date" value={recurrente.fecha_inicio} onChange={(e) => setRecurrente({ ...recurrente, fecha_inicio: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
              <input type="number" min={1} max={52} value={recurrente.cant_semanas} onChange={(e) => setRecurrente({ ...recurrente, cant_semanas: Number(e.target.value) })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <input required placeholder="Enlace de videoconferencia" value={recurrente.meet_url} onChange={(e) => setRecurrente({ ...recurrente, meet_url: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <button disabled={recurrenteMut.isPending} className="w-full py-2 text-sm font-semibold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:opacity-50">Generar instancias</button>
          </form>

          <form onSubmit={(e) => { e.preventDefault(); unicoMut.mutate(); }} className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
            <h2 className="font-bold text-slate-800">Encuentro único</h2>
            <input required placeholder="Título" value={unico.titulo} onChange={(e) => setUnico({ ...unico, titulo: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input required type="datetime-local" value={unico.fecha_hora} onChange={(e) => setUnico({ ...unico, fecha_hora: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input placeholder="Enlace de videoconferencia" value={unico.meet_url} onChange={(e) => setUnico({ ...unico, meet_url: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <button disabled={unicoMut.isPending} className="w-full py-2 text-sm font-semibold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:opacity-50">Crear encuentro</button>
          </form>
        </div>
      )}

      {materiaId && (
        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 font-bold text-slate-800">Instancias programadas</div>
          <div className="divide-y divide-slate-100">
            {instancias?.length === 0 && <div className="p-5 text-sm text-slate-400">No hay encuentros para esta materia.</div>}
            {instancias?.map((inst) => <InstanciaRow key={inst.id} inst={inst} onSave={(estado, video_url, comentario) => updateMut.mutate({ id: inst.id, estado, video_url, comentario })} />)}
          </div>
        </section>
      )}
    </div>
  );
};

const InstanciaRow = ({ inst, onSave }: { inst: InstanciaEncuentro; onSave: (estado: string, video: string, comentario: string) => void }) => {
  const [estado, setEstado] = useState(inst.estado);
  const [video, setVideo] = useState(inst.video_url ?? '');
  const [comentario, setComentario] = useState(inst.comentario ?? '');
  return (
    <div className="p-4 grid grid-cols-1 md:grid-cols-5 gap-2 items-center text-sm">
      <div className="font-medium text-slate-800">{inst.titulo}<div className="text-xs text-slate-400">{new Date(inst.fecha_hora).toLocaleString()}</div></div>
      <select value={estado} onChange={(e) => setEstado(e.target.value as never)} className="rounded-lg border border-slate-300 px-2 py-1.5">
        {ESTADOS_ENCUENTRO.map((s) => <option key={s} value={s}>{s}</option>)}
      </select>
      <input placeholder="Enlace de grabación" value={video} onChange={(e) => setVideo(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-1.5" />
      <input placeholder="Comentario" value={comentario} onChange={(e) => setComentario(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-1.5" />
      <button onClick={() => onSave(estado, video, comentario)} className="py-1.5 text-xs font-semibold text-white bg-slate-700 rounded-lg hover:bg-slate-800">Guardar</button>
    </div>
  );
};
