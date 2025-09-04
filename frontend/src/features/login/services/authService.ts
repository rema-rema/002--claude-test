import axios, { AxiosInstance } from 'axios';
import { LoginRequest, TokenResponse, AuthStatus } from '../types/auth';

class AuthService {
  private api: AxiosInstance;

  constructor() {
    // 動的にAPIエンドポイントを決定
    const baseURL = typeof window !== 'undefined' 
      ? `http://${window.location.hostname}:8000`
      : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    this.api = axios.create({
      baseURL,
      timeout: 10000,
      withCredentials: true, // Include cookies in requests
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          this.handleUnauthorized();
        }
        return Promise.reject(error);
      }
    );
  }

  private handleUnauthorized(): void {
    // Clear auth state and redirect to login
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth-storage');
      window.location.href = '/login';
    }
  }

  async login(loginRequest: LoginRequest): Promise<TokenResponse> {
    try {
      const response = await this.api.post<TokenResponse>('/api/auth/login', loginRequest);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  }

  async mockLogin(email: string, password: string): Promise<any> {
    try {
      const response = await this.api.post('/api/auth/mock-login', { email, password });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Mock login failed');
    }
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/api/auth/mock-logout');
    } catch (error: any) {
      // Even if logout fails on server, clear client state
      console.warn('Logout request failed:', error);
    }
  }

  async refreshToken(): Promise<TokenResponse> {
    try {
      const response = await this.api.post<TokenResponse>('/api/auth/refresh');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Token refresh failed');
    }
  }

  async getAuthStatus(): Promise<AuthStatus> {
    try {
      const response = await this.api.get<AuthStatus>('/api/auth/status');
      return response.data;
    } catch (error: any) {
      return {
        is_authenticated: false,
        user: undefined,
        session: undefined,
      };
    }
  }

  async checkAuth(): Promise<any> {
    try {
      const response = await this.api.get('/api/auth/mock-me');
      return response.data;
    } catch (error: any) {
      return {
        is_authenticated: false,
        user: null,
      };
    }
  }

  async getCurrentUser(): Promise<AuthStatus> {
    try {
      const response = await this.api.get<AuthStatus>('/api/auth/me');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get current user');
    }
  }

  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error: any) {
      throw new Error('Backend health check failed');
    }
  }
}

export const authService = new AuthService();