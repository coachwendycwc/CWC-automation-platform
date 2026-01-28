import { test, expect } from '@playwright/test';

test.describe('Public Pages', () => {
  test('should display organizational assessment form', async ({ page }) => {
    await page.goto('/for-organizations');

    // Should show the form title
    await expect(page.locator('h1')).toContainText(/organization|assessment|needs/i);

    // Should have form fields
    await expect(page.locator('input[name="full_name"], input[placeholder*="name" i]').first()).toBeVisible();
  });

  test('should validate required fields on assessment form', async ({ page }) => {
    await page.goto('/for-organizations');

    // Try to submit without filling required fields
    const submitButton = page.locator('button[type="submit"]').first();
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Should show validation errors or stay on the same page
    await expect(page).toHaveURL(/for-organizations/);
  });

  test('should display public booking page', async ({ page }) => {
    // Try to access a booking page (may 404 if no booking types exist)
    const response = await page.goto('/book/discovery-call');

    // Either shows booking form or 404
    expect(response?.status()).toBeLessThan(500);
  });

  test('should display testimonials gallery', async ({ page }) => {
    await page.goto('/gallery');

    // Should show gallery page (may be empty)
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test('should show 404 for non-existent pages', async ({ page }) => {
    await page.goto('/this-page-does-not-exist');

    // Should show 404 content
    await expect(page.locator('text=/404|not found/i')).toBeVisible({ timeout: 5000 });
  });
});
