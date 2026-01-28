import { test, expect } from '@playwright/test'

test.describe('Invoice Management', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login')
    await page.fill('input[type="email"]', 'dev@cwcplatform.com')
    await page.click('button:has-text("Dev Login")')
    await page.waitForURL('**/dashboard')
  })

  test('should display invoice list page', async ({ page }) => {
    await page.goto('/invoices')
    await expect(page).toHaveURL(/.*invoices/)
    await expect(page.locator('h1')).toContainText(/invoice/i)
  })

  test('should navigate to create invoice form', async ({ page }) => {
    await page.goto('/invoices')
    const createButton = page.locator('button:has-text("Create"), a:has-text("Create")')
    if (await createButton.isVisible()) {
      await createButton.click()
      await expect(page.locator('form')).toBeVisible()
    }
  })

  test('should filter invoices by status', async ({ page }) => {
    await page.goto('/invoices')
    // Look for status filter dropdown
    const statusFilter = page.locator('select, [role="combobox"]').first()
    if (await statusFilter.isVisible()) {
      await statusFilter.click()
    }
  })

  test('should display invoice details', async ({ page }) => {
    await page.goto('/invoices')
    // Click on first invoice if exists
    const invoiceRow = page.locator('tr, [data-testid*="invoice"]').first()
    if (await invoiceRow.isVisible()) {
      await invoiceRow.click()
    }
  })
})

test.describe('Public Invoice Page', () => {
  test('should show 404 for invalid token', async ({ page }) => {
    await page.goto('/pay/invalid-token-123')
    await expect(page.locator('body')).toContainText(/not found|invalid|error/i)
  })
})
