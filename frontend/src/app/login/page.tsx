'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthState } from '@/features/login/hooks/useAuth';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthState();
  const [isButtonLoading, setIsButtonLoading] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    // 初回マウント時に認証状態をチェック
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const currentHost = window.location.hostname;
      const apiUrl = `http://${currentHost}:8000`;
      const response = await fetch(`${apiUrl}/api/auth/mock-me`, {
        credentials: 'include'
      });
      const data = await response.json();
      
      if (data.is_authenticated) {
        // 既にログイン済みなら直接ダッシュボードへ
        router.push('/dashboard');
        return;
      }
    } catch (error) {
      console.log('Not authenticated');
    } finally {
      setIsCheckingAuth(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleGoogleLogin = async () => {
    // テスト用の自動ログイン (後でGoogle OAuth実装予定)
    setIsButtonLoading(true);
    try {
      // 動的にAPIエンドポイントを決定
      const currentHost = window.location.hostname;
      const apiUrl = `http://${currentHost}:8000`;
      
      const response = await fetch(`${apiUrl}/api/auth/mock-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123'
        })
      });
      
      const data = await response.json();
      console.log('Login response:', data);
      
      if (response.ok && data.success) {
        // 少し待ってからリダイレクト
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 500);
      } else {
        console.error('Login failed:', data);
        setIsButtonLoading(false);
        alert('ログインに失敗しました。もう一度お試しください。');
      }
    } catch (error) {
      console.error('Login error:', error);
      // ネットワークエラーの場合のみアラート表示
      if (error instanceof TypeError && error.message.includes('fetch')) {
        alert('ネットワークエラーが発生しました。接続を確認してください。');
      }
      setIsButtonLoading(false);
    }
  };

  if (isCheckingAuth || isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">認証状態を確認中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col justify-center px-6">
      <div className="max-w-md w-full mx-auto">
        <div className="bg-white rounded-3xl shadow-xl p-8">
          {/* App Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-blue-600 rounded-3xl flex items-center justify-center shadow-lg">
              <span className="text-white text-4xl font-bold">M</span>
            </div>
          </div>

          {/* App Title */}
          <h1 className="text-2xl font-bold text-center text-gray-800 mb-2">
            MyAppへようこそ
          </h1>
          <p className="text-sm text-center text-blue-500 mb-8">
            続行するにはログインしてください
          </p>

          {/* Google Login Button */}
          <button
            onClick={handleGoogleLogin}
            disabled={isButtonLoading}
            className="w-full bg-white border border-gray-300 rounded-full py-3 px-4 flex items-center justify-center hover:shadow-md transition-shadow duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isButtonLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 mr-3"></div>
                <span className="text-gray-700 font-medium">ログイン中...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span className="text-gray-700 font-medium">Googleでログイン</span>
              </>
            )}
          </button>

          {/* Security Notice */}
          <div className="mt-6 flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 8a6 6 0 01-7.743 5.743L10 14l-1 1-1 1H6v2H2v-4l4.257-4.257A6 6 0 1118 8zm-6-4a1 1 0 100 2 2 2 0 012 2 1 1 0 102 0 4 4 0 00-4-4z" clipRule="evenodd"/>
            </svg>
            <span className="text-xs text-blue-400">安全な接続で保護されています</span>
          </div>
        </div>
      </div>
    </div>
  );
}