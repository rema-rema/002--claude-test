import { test, expect } from '@playwright/test';

test('intentional failure test', async ({ page }) => {
  // Discord通知の失敗時フローをテスト
  await page.goto('data:text/html,<html><body><h1>Test Page</h1></body></html>');
  
  // 意図的に失敗させる（存在しない要素を探す）
  await expect(page.locator('#this-element-does-not-exist')).toBeVisible({
    timeout: 5000
  });
});