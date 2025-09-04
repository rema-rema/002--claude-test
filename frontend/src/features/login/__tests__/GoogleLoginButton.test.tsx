import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GoogleLoginButton } from '../components/GoogleLoginButton';
import { useAuthState } from '../hooks/useAuth';
import { authService } from '../services/authService';

// Mock the auth hook
jest.mock('../hooks/useAuth');
const mockUseAuthState = useAuthState as jest.MockedFunction<typeof useAuthState>;

// Mock the auth service
jest.mock('../services/authService');
const mockAuthService = authService as jest.Mocked<typeof authService>;

describe('GoogleLoginButton', () => {
  const mockLogin = jest.fn();
  const mockSetLoading = jest.fn();
  const mockSetError = jest.fn();
  const mockClearError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuthState.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: mockLogin,
      logout: jest.fn(),
      setLoading: mockSetLoading,
      setError: mockSetError,
      clearError: mockClearError,
    });
  });

  it('renders Google login button', () => {
    render(<GoogleLoginButton />);
    
    expect(screen.getByTestId('google-login-button')).toBeInTheDocument();
  });

  it('handles successful login', async () => {
    const mockTokenResponse = {
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        is_active: true,
        is_verified: true,
        created_at: '2025-08-29T00:00:00Z',
        updated_at: '2025-08-29T00:00:00Z',
      },
    };

    mockAuthService.login.mockResolvedValue(mockTokenResponse);
    
    const onSuccess = jest.fn();
    render(<GoogleLoginButton onSuccess={onSuccess} />);
    
    const button = screen.getByTestId('google-login-button');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockSetLoading).toHaveBeenCalledWith(true);
      expect(mockClearError).toHaveBeenCalled();
      expect(mockAuthService.login).toHaveBeenCalledWith({
        access_token: 'mock-credential',
        provider: 'google',
      });
      expect(mockLogin).toHaveBeenCalledWith(mockTokenResponse);
      expect(onSuccess).toHaveBeenCalled();
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('handles login error', async () => {
    const error = new Error('Login failed');
    mockAuthService.login.mockRejectedValue(error);
    
    const onError = jest.fn();
    render(<GoogleLoginButton onError={onError} />);
    
    const button = screen.getByTestId('google-login-button');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockSetError).toHaveBeenCalledWith('Login failed');
      expect(onError).toHaveBeenCalledWith('Login failed');
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('disables button when disabled prop is true', () => {
    render(<GoogleLoginButton disabled={true} />);
    
    const button = screen.getByTestId('google-login-button');
    expect(button).toBeDisabled();
  });
});