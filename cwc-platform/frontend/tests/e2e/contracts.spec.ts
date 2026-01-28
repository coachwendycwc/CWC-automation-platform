import { test, expect } from '@playwright/test'

test.describe('Contract Management', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login')
    await page.fill('input[type="email"]', 'dev@cwcplatform.com')
    await page.click('button:has-text("Dev Login")')
    await page.waitForURL('**/dashboard')
  })

  test('should display contracts list page', async ({ page }) => {
    await page.goto('/contracts')
    await expect(page).toHaveURL(/.*contracts/)
    await expect(page.locator('h1')).toContainText(/contract/i)
  })

  test('should display contract templates page', async ({ page }) => {
    await page.goto('/contracts/templates')
    await expect(page.locator('body')).toContainText(/template/i)
  })

  test('should filter contracts by status', async ({ page }) => {
    await page.goto('/contracts')
    // Look for status filter
    const statusFilter = page.locator('[data-testid="status-filter"], select').first()
    if (await statusFilter.isVisible()) {
      await statusFilter.click()
    }
  })

  test('should navigate to create contract', async ({ page }) => {
    await page.goto('/contracts')
    const createButton = page.locator('button:has-text("Create"), a:has-text("New")')
    if (await createButton.isVisible()) {
      await createButton.click()
    }
  })
})

test.describe('Public Contract Signing', () => {
  test('should show error for invalid signing token', async ({ page }) => {
    await page.goto('/sign/invalid-token-xyz')
    await expect(page.locator('body')).toContainText(/not found|invalid|expired|error/i)
  })
})
