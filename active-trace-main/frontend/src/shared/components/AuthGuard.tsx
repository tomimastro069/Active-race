import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/shared/contexts/AuthContext';

interface AuthGuardProps {
  requiredRoles?: string[];
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ requiredRoles }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-gray-50 text-gray-600">
        <span className="text-lg animate-pulse">Cargando sesión...</span>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    // Redirigir al login guardando la ruta intentada
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRoles && requiredRoles.length > 0) {
    const hasRole = requiredRoles.some((role) => user.roles.includes(role));
    if (!hasRole) {
      // Redirigir si no tiene permisos/roles
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <Outlet />;
};
