import { test, expect } from '@playwright/test';

test('エラー確認テスト - 通知なしであることを確認', async ({ page }) => {
  // 意図的にテストを失敗させる
  await page.goto('data:text/html,<h1>エラーテスト</h1>');
  
  // このアサーションは必ず失敗する
  await expect(page.locator('h1')).toHaveText('存在しないテキスト');
});