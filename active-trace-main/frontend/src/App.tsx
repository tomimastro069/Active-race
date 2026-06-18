import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/shared/contexts/AuthContext';
import { AuthGuard } from '@/shared/components/AuthGuard';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { Layout } from '@/shared/components/Layout';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { ComisionesListPage } from '@/features/academico-docente/pages/ComisionesListPage';
import { ComisionDashboard } from '@/features/academico-docente/pages/ComisionDashboard';
import { MonitorSeguimientoPage } from '@/features/academico-docente/pages/MonitorSeguimientoPage';
import { PadronPage } from '@/features/academico-docente/pages/PadronPage';
import { EquiposPage } from '@/features/coordinacion/pages/EquiposPage';
import { AvisosPage } from '@/features/coordinacion/pages/AvisosPage';
import { TareasPage } from '@/features/coordinacion/pages/TareasPage';
import { MonitorCoordinacionPage } from '@/features/coordinacion/pages/MonitorCoordinacionPage';
import { UsuariosPage } from '@/features/coordinacion/pages/UsuariosPage';
import { PerfilPage } from '@/features/perfil/pages/PerfilPage';
import { InboxPage } from '@/features/mensajeria/pages/InboxPage';
import { EncuentrosPage } from '@/features/encuentros/pages/EncuentrosPage';
import { GuardiasPage } from '@/features/guardias/pages/GuardiasPage';
import './index.css';


const UnauthorizedPlaceholder = () => (
  <div className="flex h-screen items-center justify-center">
    <h1 className="text-2xl text-red-600 font-bold">Acceso Denegado (403)</h1>
  </div>
);

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/unauthorized" element={<UnauthorizedPlaceholder />} />
            
            {/* Rutas Privadas protegidas por AuthGuard y envueltas en Layout */}
            <Route element={<AuthGuard />}>
              <Route element={<Layout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/comisiones" element={<ComisionesListPage />} />
                <Route path="/comisiones/:materiaId/:cohorteId" element={<ComisionDashboard />} />
                <Route path="/monitor-seguimiento" element={<MonitorSeguimientoPage />} />
                <Route path="/padron" element={<PadronPage />} />
                <Route path="/equipos" element={<EquiposPage />} />
                <Route path="/usuarios" element={<UsuariosPage />} />
                <Route path="/avisos" element={<AvisosPage />} />
                <Route path="/tareas" element={<TareasPage />} />
                <Route path="/monitor-coordinacion" element={<MonitorCoordinacionPage />} />
                <Route path="/encuentros" element={<EncuentrosPage />} />
                <Route path="/guardias" element={<GuardiasPage />} />
                <Route path="/perfil" element={<PerfilPage />} />
                <Route path="/inbox" element={<InboxPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Route>
            </Route>
            
            {/* Catch-all fallback */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
