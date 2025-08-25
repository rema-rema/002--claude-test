import { test, expect } from '@playwright/test';

test('success notification test', async ({ page }) => {
  // シンプルな成功テスト
  await page.goto('data:text/html,<html><body><h1>Success Test Page</h1><p>This test should pass</p></body></html>');
  
  // 成功する検証
  await expect(page.locator('h1')).toHaveText('Success Test Page');
  await expect(page.locator('p')).toContainText('This test should pass');
});

test('another success test', async ({ page }) => {
  // 複数テストの成功パターン
  await page.goto('data:text/html,<html><body><div id="content">Content Loaded</div></body></html>');
  
  await expect(page.locator('#content')).toBeVisible();
  await expect(page.locator('#content')).toHaveText('Content Loaded');
});