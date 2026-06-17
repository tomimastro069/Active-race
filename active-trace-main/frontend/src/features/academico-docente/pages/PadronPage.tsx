import { useState, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../shared/services/api';

interface VersionPadron {
  id: string;
  materia_id: string;
  cohorte_id: string;
  cantidad_entradas: number;
  created_at: string;
}

const padronService = {
  importarCSV: async (materiaId: string, cohorteId: string, file: File): Promise<VersionPadron> => {
    const formData = new FormData();
    formData.append('materia_id', materiaId);
    formData.append('cohorte_id', cohorteId);
    formData.append('file', file);
    const response = await api.post<VersionPadron>('/padron/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getActiveVersion: async (materiaId: string, cohorteId: string): Promise<VersionPadron | null> => {
    const response = await api.get<VersionPadron | null>('/padron/active', {
      params: { materia_id: materiaId, cohorte_id: cohorteId },
    });
    return response.data;
  },
};

export const PadronPage = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [materiaId, setMateriaId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const { data: activeVersion } = useQuery({
    queryKey: ['padron-active', materiaId, cohorteId],
    queryFn: () => padronService.getActiveVersion(materiaId, cohorteId),
    enabled: materiaId.length === 36 && cohorteId.length === 36,
  });

  const importMutation = useMutation({
    mutationFn: () => padronService.importarCSV(materiaId, cohorteId, file!),
    onSuccess: () => {
      setFile(null);
      setFileName(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      queryClient.invalidateQueries({ queryKey: ['padron-active'] });
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setFileName(f.name);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !materiaId || !cohorteId) return;
    importMutation.mutate();
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Importar Padrón de Alumnos</h1>
        <p className="text-slate-500 mt-1">
          Subí el CSV exportado desde Moodle para cargar el padrón de una comisión.
        </p>
      </header>

      {/* Instrucciones */}
      <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm font-semibold text-amber-800 mb-2">📋 Formato esperado del CSV</p>
        <p className="text-xs text-amber-700 font-mono bg-amber-100 rounded p-2">
          email,nombre,apellidos,comision,regional<br />
          juan@mail.com,Juan,Pérez,A,BsAs<br />
          ana@mail.com,Ana,García,B,Córdoba
        </p>
        <p className="text-xs text-amber-600 mt-2">
          Los campos <strong>email, nombre, apellidos</strong> son obligatorios. El delimitador puede ser coma (,) o punto y coma (;).
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Materia (UUID)</label>
            <input
              required
              type="text"
              value={materiaId}
              onChange={(e) => setMateriaId(e.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Cohorte (UUID)</label>
            <input
              required
              type="text"
              value={cohorteId}
              onChange={(e) => setCohorteId(e.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            />
          </div>
        </div>

        {/* Versión activa actual */}
        {activeVersion && (
          <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 text-sm">
            <span className="font-medium text-blue-800">Versión activa:</span>{' '}
            <span className="text-blue-700">
              {activeVersion.cantidad_entradas} alumnos · importado el{' '}
              {new Date(activeVersion.created_at).toLocaleDateString()}
            </span>
            <p className="text-blue-600 text-xs mt-1">
              Al importar un nuevo CSV, la versión anterior quedará reemplazada.
            </p>
          </div>
        )}

        {/* File drop zone */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Archivo CSV</label>
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
              fileName
                ? 'border-indigo-300 bg-indigo-50'
                : 'border-slate-200 bg-slate-50 hover:border-indigo-300 hover:bg-indigo-50'
            }`}
          >
            {fileName ? (
              <div>
                <p className="text-2xl mb-2">📄</p>
                <p className="text-sm font-medium text-indigo-700">{fileName}</p>
                <p className="text-xs text-slate-500 mt-1">Clic para cambiar el archivo</p>
              </div>
            ) : (
              <div>
                <p className="text-2xl mb-2">📂</p>
                <p className="text-sm font-medium text-slate-600">Arrastrá o hacé clic para seleccionar</p>
                <p className="text-xs text-slate-400 mt-1">Archivos .csv hasta 10MB</p>
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        <button
          type="submit"
          disabled={!file || !materiaId || !cohorteId || importMutation.isPending}
          className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {importMutation.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Importando...
            </span>
          ) : 'Importar Padrón'}
        </button>

        {importMutation.isSuccess && (
          <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-green-800 text-sm">
            ✅ Padrón importado correctamente con{' '}
            <strong>{importMutation.data.cantidad_entradas}</strong> alumnos.
          </div>
        )}

        {importMutation.isError && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
            ❌ Error al importar: {(importMutation.error as any)?.response?.data?.detail || 'Error desconocido.'}
          </div>
        )}
      </form>
    </div>
  );
};
