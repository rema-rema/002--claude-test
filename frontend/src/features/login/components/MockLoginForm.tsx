'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../services/authService';

export function MockLoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await authService.mockLogin(email, password);
      if (response.success) {
        router.push('/dashboard');
      } else {
        setError('ログインに失敗しました');
      }
    } catch (err) {
      setError('メールアドレスまたはパスワードが正しくありません');
    } finally {
      setIsLoading(false);
    }
  };

  const fillTestAccount = (type: 'test' | 'admin') => {
    if (type === 'test') {
      setEmail('test@example.com');
      setPassword('password123');
    } else {
      setEmail('admin@example.com');
      setPassword('admin123');
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            メールアドレス
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="test@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            パスワード
          </label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="password123"
          />
        </div>

        {error && (
          <div className="text-red-600 text-sm text-center">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {isLoading ? 'ログイン中...' : 'ログイン'}
        </button>
      </form>

      <div className="border-t pt-4">
        <p className="text-sm text-gray-600 mb-2">テストアカウント:</p>
        <div className="space-x-2">
          <button
            onClick={() => fillTestAccount('test')}
            className="text-sm text-indigo-600 hover:text-indigo-500"
          >
            テストユーザー
          </button>
          <span className="text-gray-400">|</span>
          <button
            onClick={() => fillTestAccount('admin')}
            className="text-sm text-indigo-600 hover:text-indigo-500"
          >
            管理者ユーザー
          </button>
        </div>
      </div>
    </div>
  );
}