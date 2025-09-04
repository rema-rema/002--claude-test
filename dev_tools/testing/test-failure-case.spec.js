import { test, expect } from '@playwright/test';

test('意図的失敗テスト - Discord通知確認用', async ({ page }) => {
  // 簡単なページを開く
  await page.goto('data:text/html,<h1>テスト失敗確認</h1><p>このページでテスト失敗を確認します</p>');
  
  // 意図的にテストを失敗させる
  await expect(page.locator('h1')).toHaveText('存在しないテキスト');
});