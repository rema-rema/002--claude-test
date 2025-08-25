import { test, expect } from '@playwright/test';

test('successful test example', async ({ page }) => {
  // シンプルな成功テスト
  await page.goto('data:text/html,<html><body><h1>Test Page</h1></body></html>');
  
  // タイトルの確認
  await expect(page.locator('h1')).toHaveText('Test Page');
});

test('failing test example', async ({ page }) => {
  // 意図的に失敗するテスト（Discord通知テスト用）
  await page.goto('data:text/html,<html><body><h1>Test Page</h1></body></html>');
  
  // 存在しない要素を探して失敗させる
  await expect(page.locator('#non-existent')).toBeVisible();
});