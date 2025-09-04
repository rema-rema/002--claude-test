'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthState } from '@/features/login/hooks/useAuth';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthState();

  useEffect(() => {
    // Redirect authenticated users to dashboard
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="loading-spinner h-8 w-8"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="loading-spinner h-8 w-8"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            002 Claude Test
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            ログインシステム with Google OAuth
          </p>
        </div>
        
        <div className="card p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            開発ステータス
          </h2>
          <div className="space-y-2">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-700">プロジェクト構造作成済み</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-700">バックエンドAPI実装済み</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-700">フロントエンド実装済み</span>
            </div>
          </div>
          
          <div className="mt-6">
            <Link
              href="/login"
              className="w-full btn btn-primary text-center block"
            >
              ログインページへ
            </Link>
          </div>
        </div>

        <div className="text-center">
          <div className="text-sm text-gray-600">
            <p>開発環境情報:</p>
            <p className="mt-1 font-mono text-xs">
              Session: {process.env.NEXT_PUBLIC_SESSION_ID || 'N/A'}
            </p>
            <p className="font-mono text-xs">
              API: {process.env.NEXT_PUBLIC_API_URL || 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}