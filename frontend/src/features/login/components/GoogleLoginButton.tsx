'use client';

import React from 'react';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { useAuthState } from '../hooks/useAuth';
import { authService } from '../services/authService';

interface GoogleLoginButtonProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
  disabled?: boolean;
}

export const GoogleLoginButton: React.FC<GoogleLoginButtonProps> = ({
  onSuccess,
  onError,
  disabled = false,
}) => {
  const { login, setLoading, setError, clearError } = useAuthState();

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      const error = 'Google認証に失敗しました';
      setError(error);
      onError?.(error);
      return;
    }

    try {
      setLoading(true);
      clearError();

      // Send Google credential to our backend
      const tokenResponse = await authService.login({
        access_token: credentialResponse.credential,
        provider: 'google',
      });

      // Update auth state
      login(tokenResponse);
      
      onSuccess?.();
    } catch (error: any) {
      const errorMessage = error.message || 'ログインに失敗しました';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    const error = 'Googleログインが中断されました';
    setError(error);
    onError?.(error);
  };

  return (
    <div className="w-full">
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={handleGoogleError}
        useOneTap={false}
        auto_select={false}
        theme="outline"
        size="large"
        width="100%"
        text="signin_with"
        shape="rectangular"
        logo_alignment="left"
      />
    </div>
  );
};