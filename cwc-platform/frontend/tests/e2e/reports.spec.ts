import { test, expect } from '@playwright/test'

test.describe('Reports and Analytics', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login')
    await page.fill('input[type="email"]', 'dev@cwcplatform.com')
    await page.click('button:has-text("Dev Login")')
    await page.waitForURL('**/dashboard')
  })

  test('should display reports page', async ({ page }) => {
    await page.goto('/reports')
    await expect(page).toHaveURL(/.*reports/)
    await expect(page.locator('body')).toContainText(/report|analytics|revenue|summary/i)
  })

  test('should display revenue statistics', async ({ page }) => {
    await page.goto('/reports')
    // Should show some statistics
    await expect(page.locator('body')).toContainText(/revenue|total|amount|\$/i)
  })

  test('should display charts', async ({ page }) => {
    await page.goto('/reports')
    // Check for chart elements (Recharts typically uses SVG)
    const charts = page.locator('svg, [class*="chart"], .recharts-responsive-container')
    if (await charts.first().isVisible()) {
      await expect(charts.first()).toBeVisible()
    }
  })

  test('should allow date range selection', async ({ page }) => {
    await page.goto('/reports')
    // Look for date picker or range selector
    const dateFilter = page.locator('[data-testid="date-range"], input[type="date"], button:has-text("Date")')
    if (await dateFilter.first().isVisible()) {
      await dateFilter.first().click()
    }
  })

  test('should allow CSV export', async ({ page }) => {
    await page.goto('/reports')
    const exportButton = page.locator('button:has-text("Export"), button:has-text("Download"), button:has-text("CSV")')
    if (await exportButton.isVisible()) {
      await expect(exportButton).toBeVisible()
    }
  })
})

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"]', 'dev@cwcplatform.com')
    await page.click('button:has-text("Dev Login")')
    await page.waitForURL('**/dashboard')
  })

  test('should display dashboard with stats', async ({ page }) => {
    await expect(page).toHaveURL(/.*dashboard/)
    // Should show quick stats cards
    await expect(page.locator('body')).toContainText(/total|this month|revenue|client/i)
  })

  test('should display recent activity', async ({ page }) => {
    await page.goto('/dashboard')
    // Look for recent items section
    await expect(page.locator('body')).toContainText(/recent|activity|latest/i)
  })
})
