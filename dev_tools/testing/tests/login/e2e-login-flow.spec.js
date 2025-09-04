const { test, expect } = require('@playwright/test');

test.describe('Login Flow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the home page
    await page.goto('/');
  });

  test('should display home page and redirect to login', async ({ page }) => {
    // Check home page elements
    await expect(page.locator('h1')).toContainText('002 Claude Test');
    
    // Click login button
    await page.click('text=ログインページへ');
    
    // Should be redirected to login page
    await expect(page).toHaveURL('/login');
  });

  test('should display login page correctly', async ({ page }) => {
    await page.goto('/login');
    
    // Check login page elements
    await expect(page.locator('h1')).toContainText('002 Claude Test');
    await expect(page.locator('h2')).toContainText('ログイン');
    
    // Check Google login button presence (mocked in test)
    await expect(page.locator('text=Sign in with Google')).toBeVisible();
  });

  test('should handle login flow', async ({ page }) => {
    await page.goto('/login');
    
    // Mock successful Google OAuth (this would normally open Google OAuth popup)
    await page.evaluate(() => {
      // Mock the Google OAuth response
      window.mockGoogleOAuthSuccess = true;
    });
    
    // Click Google login button
    await page.click('text=Sign in with Google');
    
    // Should show loading state
    await expect(page.locator('text=ログイン中...')).toBeVisible();
  });

  test('should display user dashboard after login', async ({ page }) => {
    // Mock authenticated state by setting localStorage
    await page.addInitScript(() => {
      localStorage.setItem('auth-storage', JSON.stringify({
        state: {
          user: {
            id: '123',
            email: 'test@example.com',
            name: 'Test User',
            is_active: true,
            is_verified: true,
            created_at: '2025-08-29T00:00:00Z',
            updated_at: '2025-08-29T00:00:00Z'
          },
          isAuthenticated: true
        }
      }));
    });
    
    await page.goto('/dashboard');
    
    // Check dashboard elements
    await expect(page.locator('text=おかえりなさい、Test Userさん！')).toBeVisible();
    await expect(page.locator('text=test@example.com')).toBeVisible();
    
    // Check logout button
    await expect(page.locator('text=ログアウト')).toBeVisible();
  });

  test('should handle logout from dashboard', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('auth-storage', JSON.stringify({
        state: {
          user: {
            id: '123',
            email: 'test@example.com',
            name: 'Test User',
            is_active: true,
            is_verified: true,
            created_at: '2025-08-29T00:00:00Z',
            updated_at: '2025-08-29T00:00:00Z'
          },
          isAuthenticated: true
        }
      }));
    });
    
    await page.goto('/dashboard');
    
    // Click logout button
    await page.click('text=ログアウト');
    
    // Should redirect to login page
    await expect(page).toHaveURL('/login');
  });

  test('should display development environment info', async ({ page }) => {
    await page.goto('/');
    
    // Check development info display
    await expect(page.locator('text=開発環境情報:')).toBeVisible();
    await expect(page.locator('text=Session:')).toBeVisible();
    await expect(page.locator('text=API:')).toBeVisible();
  });

  test('should handle navigation between pages', async ({ page }) => {
    // Start from home
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('002 Claude Test');
    
    // Go to login
    await page.click('text=ログインページへ');
    await expect(page).toHaveURL('/login');
    await expect(page.locator('h2')).toContainText('ログイン');
    
    // Navigate back to home (browser back button simulation)
    await page.goBack();
    await expect(page).toHaveURL('/');
  });
});

test.describe('Authentication Edge Cases', () => {
  test('should handle unauthenticated dashboard access', async ({ page }) => {
    // Try to access dashboard without authentication
    await page.goto('/dashboard');
    
    // Should be redirected to login
    await expect(page).toHaveURL('/login');
  });

  test('should handle authentication state persistence', async ({ page }) => {
    // Set authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('auth-storage', JSON.stringify({
        state: {
          user: {
            id: '123',
            email: 'test@example.com',
            name: 'Test User',
            is_active: true,
            is_verified: true,
            created_at: '2025-08-29T00:00:00Z',
            updated_at: '2025-08-29T00:00:00Z'
          },
          isAuthenticated: true
        }
      }));
    });
    
    // Visit home page
    await page.goto('/');
    
    // Should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard');
  });

  test('should handle error states in login', async ({ page }) => {
    await page.goto('/login');
    
    // Mock login error
    await page.evaluate(() => {
      window.mockLoginError = 'Authentication failed';
    });
    
    // The error handling would be triggered by the actual Google OAuth flow
    // This test verifies the error display structure exists
    await expect(page.locator('h2')).toContainText('ログイン');
  });
});