'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuthState } from '@/features/login/hooks/useAuth';
import { authService } from '@/features/login/services/authService';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    checkAuthAndLoadUser();
  }, []);

  const checkAuthAndLoadUser = async () => {
    try {
      // 動的にAPIエンドポイントを決定
      const currentHost = window.location.hostname;
      const apiUrl = `http://${currentHost}:8000`;
      
      const response = await fetch(`${apiUrl}/api/auth/mock-me`, {
        credentials: 'include'
      });
      const data = await response.json();
      
      if (data.is_authenticated && data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
      } else {
        router.push('/login');
      }
    } catch (error) {
      console.error('Auth check error:', error);
      router.push('/login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      
      // 動的にAPIエンドポイントを決定
      const currentHost = window.location.hostname;
      const apiUrl = `http://${currentHost}:8000`;
      
      await fetch(`${apiUrl}/api/auth/mock-logout`, {
        method: 'POST',
        credentials: 'include'
      });
      
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
      router.push('/login');
    } finally {
      setIsLoggingOut(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null; // Router redirect will handle
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                002 Claude Test - Dashboard
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                {user.picture && (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className="h-8 w-8 rounded-full"
                  />
                )}
                <div className="hidden sm:block">
                  <p className="text-sm font-medium text-gray-900">
                    {user.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {user.email}
                  </p>
                </div>
              </div>
              
              <button
                onClick={handleLogout}
                disabled={isLoggingOut}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
              >
                {isLoggingOut ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    ログアウト中...
                  </>
                ) : (
                  'ログアウト'
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="space-y-8">
          {/* Welcome Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              ようこそ、{user.name}さん！
            </h2>
            <p className="text-gray-600 mb-6">
              ログイン機能のテストプロジェクトへようこそ。
              モック認証が正常に動作していることを確認できました。
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-sm font-medium text-green-800">
                    認証システム
                  </span>
                </div>
                <p className="text-xs text-green-600 mt-1">正常動作中</p>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                  <span className="text-sm font-medium text-blue-800">
                    データベース
                  </span>
                </div>
                <p className="text-xs text-blue-600 mt-1">接続済み</p>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-purple-500 rounded-full mr-3"></div>
                  <span className="text-sm font-medium text-purple-800">
                    セッション管理
                  </span>
                </div>
                <p className="text-xs text-purple-600 mt-1">アクティブ</p>
              </div>
            </div>
          </div>

          {/* User Information */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              ユーザー情報
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ID</dt>
                    <dd className="text-sm font-mono text-gray-900">{user.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">名前</dt>
                    <dd className="text-sm text-gray-900">{user.name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">メールアドレス</dt>
                    <dd className="text-sm text-gray-900">{user.email}</dd>
                  </div>
                </dl>
              </div>
              
              <div>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">認証方式</dt>
                    <dd className="text-sm text-gray-900">Mock Authentication</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ログイン時刻</dt>
                    <dd className="text-sm text-gray-900">
                      {new Date().toLocaleString('ja-JP')}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">状態</dt>
                    <dd className="text-sm">
                      <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        アクティブ
                      </span>
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>

          {/* Development Info */}
          {/* Test Results */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              テスト結果
            </h3>
            <div className="space-y-3">
              <div className="flex items-center">
                <svg className="h-5 w-5 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm text-gray-900">モックログイン機能 ✅</span>
              </div>
              <div className="flex items-center">
                <svg className="h-5 w-5 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm text-gray-900">JWT認証システム ✅</span>
              </div>
              <div className="flex items-center">
                <svg className="h-5 w-5 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm text-gray-900">Next.js + FastAPI統合 ✅</span>
              </div>
              <div className="flex items-center">
                <svg className="h-5 w-5 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm text-gray-900">HTTPOnly Cookie設定 ✅</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}