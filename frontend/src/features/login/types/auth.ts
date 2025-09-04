export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  profile_data?: Record<string, any>;
  preferences?: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginRequest {
  access_token: string;
  provider: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthStatus {
  is_authenticated: boolean;
  user?: User;
  session?: any;
}

export interface GoogleUser {
  id: string;
  email: string;
  verified_email: boolean;
  name: string;
  given_name: string;
  family_name: string;
  picture: string;
  locale: string;
}