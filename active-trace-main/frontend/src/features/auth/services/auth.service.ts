import { api, setAccessToken } from '@/shared/services/api';
import type { AuthUser, AuthTokens } from '@/shared/types/auth.types';

export interface LoginCredentials {
  email: string;
  password: string;
}

const persistTokens = (tokens: AuthTokens) => {
  if (tokens.access_token) {
    setAccessToken(tokens.access_token);
  }
  if (tokens.refresh_token) {
    localStorage.setItem('refresh_token', tokens.refresh_token);
  }
};

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/login', credentials);
    // Con requires_2fa, access_token es un token TEMPORAL para /auth/verify-2fa:
    // no es una sesión y no debe persistirse.
    if (!response.data.requires_2fa) {
      persistTokens(response.data);
    }
    return response.data;
  },

  verify2fa: async (temporaryToken: string, totpCode: string): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/verify-2fa', {
      temporary_token: temporaryToken,
      totp_code: totpCode,
    });
    persistTokens(response.data);
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
