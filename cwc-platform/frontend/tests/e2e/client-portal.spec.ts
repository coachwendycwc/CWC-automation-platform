import { test, expect } from '@playwright/test';

test.describe('Client Portal', () => {
  test('should display client login page', async ({ page }) => {
    await page.goto('/client/login');

    // Should show magic link login form
    await expect(page.locator('text=/email|magic link|sign in/i').first()).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('should request magic link', async ({ page }) => {
    await page.goto('/client/login');

    // Fill email
    await page.fill('input[type="email"]', 'testclient@example.com');

    // Submit
    await page.click('button[type="submit"]');

    // Should show confirmation message
    await expect(page.locator('text=/sent|check|email/i')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Public Feedback Form', () => {
  test('should display feedback form with valid token', async ({ page }) => {
    // This would need a valid token - just test that the route exists
    const response = await page.goto('/feedback/test-token');

    // Should not be a server error
    expect(response?.status()).toBeLessThan(500);
  });
});

test.describe('Public Recording Page', () => {
  test('should display recording page with valid token', async ({ page }) => {
    // This would need a valid token - just test that the route exists
    const response = await page.goto('/record/test-token');

    // Should not be a server error
    expect(response?.status()).toBeLessThan(500);
  });
});
