import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/shared/contexts/AuthContext';
import { AuthGuard } from '@/shared/components/AuthGuard';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import './index.css';

const DashboardPlaceholder = () => (
  <div className="p-8">
    <h1 className="text-3xl font-bold">Dashboard (Protegido)</h1>
    <p className="mt-4 text-gray-600">Bienvenido al sistema.</p>
  </div>
);

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
            
            {/* Rutas Privadas protegidas por AuthGuard */}
            <Route element={<AuthGuard />}>
              <Route path="/dashboard" element={<DashboardPlaceholder />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
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
