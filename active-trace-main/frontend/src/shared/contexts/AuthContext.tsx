import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { AuthUser, AuthState } from '@/shared/types/auth.types';
import { authService } from '@/features/auth/services/auth.service';
import { setAccessToken } from '@/shared/services/api';

interface AuthContextType extends AuthState {
  loginUser: (user: AuthUser, accessToken: string) => void;
  logoutUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  useEffect(() => {
    const initializeAuth = async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        setState({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }

      try {
        // Llamada a me() para obtener el usuario actual.
        // Si no hay access_token, el backend retornará 401 y el interceptor de api.ts
        // hará el refresh transparente.
        const user = await authService.me();
        setState({ user, isAuthenticated: true, isLoading: false });
      } catch (error) {
        setState({ user: null, isAuthenticated: false, isLoading: false });
      }
    };

    initializeAuth();
  }, []);

  const loginUser = (user: AuthUser, accessToken: string) => {
    setAccessToken(accessToken);
    setState({ user, isAuthenticated: true, isLoading: false });
  };

  const logoutUser = async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    await authService.logout();
    setState({ user: null, isAuthenticated: false, isLoading: false });
  };

  return (
    <AuthContext.Provider value={{ ...state, loginUser, logoutUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
