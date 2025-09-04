import { test, expect } from '@playwright/test';

test('multichannel-notify疎通確認テスト', async ({ page }) => {
  // Google にアクセス
  await page.goto('https://www.google.com');
  
  // タイトルを確認
  await expect(page).toHaveTitle(/Google/);
  
  console.log('✅ テスト実行成功');
});