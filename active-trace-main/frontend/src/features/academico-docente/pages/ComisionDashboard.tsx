import { createContext, useContext, useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { academicoService } from '../services/academico.service';
import type { CommissionContextType } from '../types/academico.types';
import { TabCalificaciones } from '../components/TabCalificaciones';
import { TabAtrasados } from '../components/TabAtrasados';
import { TabComunicaciones } from '../components/TabComunicaciones';
import { TabTrabajosSinCorregir } from '../components/TabTrabajosSinCorregir';

const CommissionContext = createContext<CommissionContextType | undefined>(undefined);

export const useCommission = () => {
  const ctx = useContext(CommissionContext);
  if (!ctx) throw new Error('useCommission must be used within CommissionProvider');
  return ctx;
};

export const ComisionDashboard = () => {
  const { materiaId, cohorteId } = useParams<{ materiaId: string; cohorteId: string }>();
  const [activeTab, setActiveTab] = useState<'calificaciones' | 'atrasados' | 'comunicaciones' | 'entregas'>('calificaciones');

  const { data: umbralData, refetch } = useQuery({
    queryKey: ['umbral', materiaId],
    queryFn: () => academicoService.getUmbral(materiaId!),
    enabled: !!materiaId,
  });

  const [umbralPct, setUmbralPct] = useState(60);

  useEffect(() => {
    if (umbralData?.umbral_pct !== undefined) {
      setUmbralPct(umbralData.umbral_pct);
    }
  }, [umbralData]);

  if (!materiaId || !cohorteId) {
    return <div>Faltan parámetros de materia o cohorte.</div>;
  }

  const contextValue: CommissionContextType = {
    materiaId,
    cohorteId,
    umbralPct,
    setUmbralPct: async (val: number) => {
      setUmbralPct(val);
      await academicoService.setUmbral(materiaId, val);
      refetch();
    }
  };

  return (
    <CommissionContext.Provider value={contextValue}>
      <div className="p-6 max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">
            Comisión {materiaId} - Cohorte {cohorteId}
          </h1>
          <p className="text-slate-500 mt-2">
            Umbral de aprobación actual: <span className="font-semibold text-slate-700">{umbralPct}%</span>
          </p>
        </header>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {(['calificaciones', 'atrasados', 'comunicaciones', 'entregas'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize transition-colors
                  ${activeTab === tab 
                    ? 'border-indigo-500 text-indigo-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab === 'entregas' ? 'Trabajos sin corregir' : tab}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-6 bg-white rounded-lg shadow min-h-[400px]">
          {activeTab === 'calificaciones' && <TabCalificaciones />}
          {activeTab === 'atrasados' && <TabAtrasados />}
          {activeTab === 'comunicaciones' && <TabComunicaciones />}
          {activeTab === 'entregas' && <TabTrabajosSinCorregir />}
        </div>
      </div>
    </CommissionContext.Provider>
  );
};
