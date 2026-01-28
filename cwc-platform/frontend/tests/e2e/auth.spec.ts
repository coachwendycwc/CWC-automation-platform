import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1, h2').first()).toContainText(/login|sign in/i);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill in invalid credentials
    await page.fill('input[type="email"], input[name="email"]', 'invalid@example.com');
    await page.fill('input[type="password"], input[name="password"]', 'wrongpassword');

    // Submit the form
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('text=/invalid|error|incorrect/i')).toBeVisible({ timeout: 5000 });
  });

  test('should login with dev credentials', async ({ page }) => {
    await page.goto('/login');

    // Look for dev login button or use email/password
    const devLoginButton = page.locator('text=/dev login/i');
    if (await devLoginButton.isVisible()) {
      await devLoginButton.click();
    } else {
      // Try logging in with test credentials
      await page.fill('input[type="email"], input[name="email"]', 'dev@cwcplatform.com');
      await page.fill('input[type="password"], input[name="password"]', 'dev123');
      await page.click('button[type="submit"]');
    }

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL(/login/, { timeout: 5000 });
  });
});
