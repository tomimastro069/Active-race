import { api, setAccessToken } from '@/shared/services/api';
import type { AuthUser, AuthTokens } from '@/shared/types/auth.types';

export interface LoginCredentials {
  email: string;
  password?: string;
  token_2fa?: string;
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/login', credentials);
    if (response.data.access_token) {
      setAccessToken(response.data.access_token);
    }
    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    return response.data;
  },

  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignore errors on logout
    } finally {
      setAccessToken(null);
      localStorage.removeItem('refresh_token');
    }
  },

  me: async (): Promise<AuthUser> => {
    const response = await api.get<AuthUser>('/auth/me');
    return response.data;
  }
};
