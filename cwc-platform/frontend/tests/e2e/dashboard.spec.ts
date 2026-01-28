import { test, expect, Page } from '@playwright/test';

// Helper function to login
async function login(page: Page) {
  await page.goto('/login');

  // Try dev login button first
  const devLoginButton = page.locator('text=/dev login/i');
  if (await devLoginButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await devLoginButton.click();
  } else {
    // Use credentials
    await page.fill('input[type="email"], input[name="email"]', 'dev@cwcplatform.com');
    await page.fill('input[type="password"], input[name="password"]', 'dev123');
    await page.click('button[type="submit"]');
  }

  // Wait for redirect to dashboard
  await page.waitForURL(/dashboard/, { timeout: 10000 });
}

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display dashboard after login', async ({ page }) => {
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.locator('h1')).toContainText(/dashboard/i);
  });

  test('should show sidebar navigation', async ({ page }) => {
    // Check for sidebar links
    await expect(page.locator('text=Contacts')).toBeVisible();
    await expect(page.locator('text=Invoices')).toBeVisible();
    await expect(page.locator('text=Contracts')).toBeVisible();
    await expect(page.locator('text=Projects')).toBeVisible();
  });

  test('should navigate to contacts page', async ({ page }) => {
    await page.click('text=Contacts');
    await expect(page).toHaveURL(/contacts/);
  });

  test('should navigate to assessments page', async ({ page }) => {
    await page.click('text=Assessments');
    await expect(page).toHaveURL(/assessments/);
  });
});

test.describe('Contacts Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/contacts');
  });

  test('should display contacts page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText(/contacts/i);
  });

  test('should have create contact button', async ({ page }) => {
    await expect(page.locator('text=/new contact|add contact|create/i').first()).toBeVisible();
  });

  test('should open create contact form', async ({ page }) => {
    const createButton = page.locator('text=/new contact|add contact|create/i').first();
    await createButton.click();

    // Should show a form or modal
    await expect(page.locator('input[name="first_name"], input[placeholder*="first" i]').first()).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Invoices Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/invoices');
  });

  test('should display invoices page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText(/invoices/i);
  });
});

test.describe('Assessments Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/assessments');
  });

  test('should display assessments page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText(/assessment/i);
  });

  test('should show stats cards', async ({ page }) => {
    // Should have status filter cards
    await expect(page.locator('text=/total|new|reviewed/i').first()).toBeVisible();
  });
});
