export interface AuthUser {
  id: string;
  tenant_id: string;
  email: string;
  roles: string[];
  impersonated_by_id?: string | null;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  refresh_token: string | null;
  requires_2fa: boolean;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
