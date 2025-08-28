import { test, expect } from '@playwright/test';

test('intentional failure demo - element not found', async ({ page }) => {
  console.log('🚨 Starting intentional failure test...');
  
  // Navigate to a simple page
  await page.goto('data:text/html,<html><head><title>Error Demo</title></head><body><h1>Simple Page</h1><button id="existing-btn">Click Me</button></body></html>');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // This should succeed
  await expect(page.locator('h1')).toContainText('Simple Page');
  
  // This will intentionally fail - looking for non-existent element
  await expect(page.locator('#non-existent-element')).toBeVisible();
  
  console.log('This message should not appear because test failed above');
});

test('intentional failure demo - wrong text assertion', async ({ page }) => {
  console.log('🚨 Starting text assertion failure test...');
  
  await page.goto('data:text/html,<html><body><h1>Hello World</h1><p>This is a test page</p></body></html>');
  await page.waitForLoadState('networkidle');
  
  // This should succeed
  await expect(page.locator('h1')).toBeVisible();
  
  // This will fail - wrong text assertion
  await expect(page.locator('h1')).toHaveText('Wrong Text Expected');
  
  console.log('This should not be reached');
});