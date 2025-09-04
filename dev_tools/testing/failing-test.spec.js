import { test, expect } from '@playwright/test';

test('failing test for notification testing', async ({ page }) => {
  await page.goto('data:text/html,<h1>Test Page</h1>');
  
  // This test is intentionally designed to fail
  await expect(page.locator('h1')).toHaveText('This text does not exist');
});