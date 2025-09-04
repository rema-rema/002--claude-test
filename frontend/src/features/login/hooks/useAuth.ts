import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User, TokenResponse } from '../types/auth';

interface AuthStore extends AuthState {
  login: (tokenResponse: TokenResponse) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAuth = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: (tokenResponse: TokenResponse) => {
        set({
          user: tokenResponse.user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        
        // Store tokens in cookies (handled by backend)
        // HTTPOnly cookies are set by the backend for security
      },

      logout: () => {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error, isLoading: false });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Auth hook for components
export const useAuthState = () => {
  const store = useAuth();
  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login: store.login,
    logout: store.logout,
    setLoading: store.setLoading,
    setError: store.setError,
    clearError: store.clearError,
  };
};