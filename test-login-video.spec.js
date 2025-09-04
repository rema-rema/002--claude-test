import { test, expect } from '@playwright/test';

test('Login to Dashboard Flow', async ({ page, context }) => {
  // ビデオ録画の設定
  await context.tracing.start({ screenshots: true, snapshots: true });
  
  // ログインページにアクセス
  await page.goto('http://192.168.1.13:3002/login');
  await page.waitForLoadState('networkidle');
  
  // ページタイトルを確認
  await expect(page).toHaveTitle(/Login System/);
  
  // ログインページの要素を確認
  const welcomeText = page.getByRole('heading', { name: 'MyAppへようこそ' });
  await expect(welcomeText).toBeVisible();
  
  // 少し待機（視覚的に分かりやすくするため）
  await page.waitForTimeout(2000);
  
  // Googleでログインボタンをクリック
  const loginButton = page.getByRole('button', { name: 'Googleでログイン' });
  await expect(loginButton).toBeVisible();
  await loginButton.click();
  
  // ダッシュボードへの遷移を待つ
  await page.waitForURL('**/dashboard', { timeout: 10000 });
  
  // ダッシュボードの要素を確認
  const dashboardTitle = page.getByRole('heading', { name: /ようこそ、.*さん！/ });
  await expect(dashboardTitle).toBeVisible();
  
  // ユーザー情報が表示されていることを確認
  await expect(page.getByText('Test User')).toBeVisible();
  await expect(page.getByText('test@example.com')).toBeVisible();
  
  // 少し待機（視覚的に分かりやすくするため）
  await page.waitForTimeout(3000);
  
  // ログアウトボタンをクリック
  const logoutButton = page.getByRole('button', { name: 'ログアウト' });
  await expect(logoutButton).toBeVisible();
  await logoutButton.click();
  
  // ログインページに戻ることを確認
  await page.waitForURL('**/login', { timeout: 5000 });
  await expect(welcomeText).toBeVisible();
  
  // 少し待機（視覚的に分かりやすくするため）
  await page.waitForTimeout(2000);
  
  // トレース保存
  await context.tracing.stop({ path: 'trace.zip' });
});