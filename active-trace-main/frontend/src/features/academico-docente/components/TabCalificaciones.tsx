import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useCommission } from '../pages/ComisionDashboard';
import { academicoService } from '../services/academico.service';
import type { PreviewCalificaciones } from '../types/academico.types';

export const TabCalificaciones = () => {
  const { materiaId, cohorteId, umbralPct, setUmbralPct } = useCommission();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewCalificaciones | null>(null);

  const previewMutation = useMutation({
    mutationFn: (file: File) => academicoService.previewCalificaciones(file),
    onSuccess: (data) => setPreview(data),
  });

  const importMutation = useMutation({
    mutationFn: () => academicoService.importarCalificaciones(materiaId, cohorteId, file!),
    onSuccess: (data) => {
      setFile(null);
      setPreview(null);
      const detalle = data.unmatched_emails.length > 0
        ? `\nEmails sin match en el padrón: ${data.unmatched_emails.join(', ')}`
        : '';
      alert(`Se importaron ${data.imported_count} calificaciones.${detalle}`);
    }
  });

  const vaciarMutation = useMutation({
    mutationFn: () => academicoService.vaciarCalificaciones(materiaId, cohorteId),
    onSuccess: () => alert('Calificaciones vaciadas correctamente'),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUmbralChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUmbralPct(Number(e.target.value));
  };

  return (
    <div className="p-6 space-y-8">
      {/* Umbral Config */}
      <section className="bg-slate-50 p-6 rounded-lg border border-slate-200">
        <h3 className="text-lg font-semibold mb-4 text-slate-800">Configuración de Umbral</h3>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-slate-700">Umbral Mínimo (%):</label>
          <input 
            type="number" 
            min="0" max="100" 
            value={umbralPct} 
            onChange={handleUmbralChange}
            className="border-gray-300 rounded-md shadow-sm w-24 p-2 border"
          />
        </div>
      </section>

      {/* Importación */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-slate-800">Importar Calificaciones</h3>
        <div className="flex gap-4 items-center">
          <input 
            type="file" 
            accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            onChange={handleFileChange}
            className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          <button 
            onClick={() => file && previewMutation.mutate(file)}
            disabled={!file || previewMutation.isPending}
            className="bg-indigo-600 text-white px-4 py-2 rounded shadow hover:bg-indigo-700 disabled:opacity-50"
          >
            {previewMutation.isPending ? 'Cargando...' : 'Previsualizar'}
          </button>
        </div>

        {preview && (
          <div className="mt-6">
            <h4 className="font-medium text-slate-700 mb-2">Columnas Detectadas</h4>
            <div className="flex flex-wrap gap-2 mb-2">
              {preview.headers.map(act => (
                <span key={act} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs">{act}</span>
              ))}
            </div>
            <p className="text-sm text-slate-500 mb-4">
              Se estima importar {preview.estimated_grades_count} calificaciones.
            </p>
            <button
              onClick={() => importMutation.mutate()}
              disabled={importMutation.isPending}
              className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700 disabled:opacity-50"
            >
              {importMutation.isPending ? 'Importando...' : 'Confirmar Importación'}
            </button>
          </div>
        )}
      </section>

      {/* Acciones destructivas */}
      <section className="pt-6 border-t border-red-100">
        <button
          onClick={() => {
            if (window.confirm('¿Está seguro de vaciar TODAS las calificaciones?')) {
              vaciarMutation.mutate();
            }
          }}
          disabled={vaciarMutation.isPending}
          className="bg-red-50 text-red-600 px-4 py-2 rounded border border-red-200 hover:bg-red-100 transition-colors text-sm font-medium disabled:opacity-50"
        >
          {vaciarMutation.isPending ? 'Vaciando...' : 'Vaciar Calificaciones'}
        </button>
      </section>
    </div>
  );
};
