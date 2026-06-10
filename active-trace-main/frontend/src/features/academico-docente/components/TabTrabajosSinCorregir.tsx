import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { academicoService } from '../services/academico.service';
import { useCommission } from '../pages/ComisionDashboard';
import type { EntregaPendiente } from '../types/academico.types';

export const TabTrabajosSinCorregir = () => {
  const { materiaId, cohorteId } = useCommission();
  const [file, setFile] = useState<File | null>(null);
  const [pendientes, setPendientes] = useState<EntregaPendiente[]>([]);

  const detectMutation = useMutation({
    mutationFn: (f: File) => academicoService.detectarTrabajosSinCorregir(materiaId, cohorteId, f),
    onSuccess: (data) => {
      setPendientes(data);
    },
    onError: (err) => {
      console.error('Error detectando trabajos sin corregir', err);
      alert('Error al cruzar los datos. Verifica el archivo LMS.');
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDetect = () => {
    if (file) {
      detectMutation.mutate(file);
    }
  };

  const handleExportCSV = () => {
    if (pendientes.length === 0) return;

    const headers = ['padron_id', 'nombre', 'apellido', 'actividad', 'importado_at'];
    const csvContent = [
      headers.join(','),
      ...pendientes.map(p => `${p.padron_id},${p.nombre},${p.apellido},${p.actividad},${p.importado_at ?? ''}`)
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `trabajos-sin-corregir-${materiaId}-${cohorteId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-4">Detección de Trabajos sin Corregir</h2>
      <p className="text-gray-600 mb-6">
        Sube el reporte de finalización del LMS para cruzarlo con las calificaciones actuales y detectar qué entregas faltan corregir.
      </p>

      <div className="flex items-end gap-4 mb-8">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Reporte LMS (CSV)</label>
          <input 
            type="file" 
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-indigo-50 file:text-indigo-700
              hover:file:bg-indigo-100"
          />
        </div>
        <button
          onClick={handleDetect}
          disabled={!file || detectMutation.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {detectMutation.isPending ? 'Cruzando Datos...' : 'Detectar'}
        </button>
      </div>

      {pendientes.length > 0 && (
        <div className="mt-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">Resultados ({pendientes.length} encontrados)</h3>
            <button
              onClick={handleExportCSV}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
            >
              Exportar CSV
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Padrón</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alumno</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actividad</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Importado</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {pendientes.map((p, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{p.padron_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{p.nombre} {p.apellido}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{p.actividad}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {p.importado_at ? new Date(p.importado_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {detectMutation.isSuccess && pendientes.length === 0 && (
        <div className="mt-8 p-4 bg-green-50 text-green-700 rounded-md">
          No se encontraron trabajos pendientes de corregir para este reporte.
        </div>
      )}
    </div>
  );
};
