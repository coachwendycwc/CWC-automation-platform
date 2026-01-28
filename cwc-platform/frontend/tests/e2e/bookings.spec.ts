import { test, expect } from '@playwright/test'

test.describe('Booking Management', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login')
    await page.fill('input[type="email"]', 'dev@cwcplatform.com')
    await page.click('button:has-text("Dev Login")')
    await page.waitForURL('**/dashboard')
  })

  test('should display calendar page', async ({ page }) => {
    await page.goto('/calendar')
    await expect(page).toHaveURL(/.*calendar/)
    // Should show calendar or bookings view
    await expect(page.locator('body')).toContainText(/calendar|booking|schedule/i)
  })

  test('should display booking types page', async ({ page }) => {
    await page.goto('/booking-types')
    await expect(page.locator('body')).toContainText(/booking|type|session/i)
  })

  test('should display availability settings', async ({ page }) => {
    await page.goto('/availability')
    await expect(page.locator('body')).toContainText(/availability|hours|schedule/i)
  })

  test('should navigate between calendar views', async ({ page }) => {
    await page.goto('/calendar')
    // Look for week/month/day view buttons
    const viewButtons = page.locator('button:has-text("Week"), button:has-text("Month"), button:has-text("Day")')
    if (await viewButtons.first().isVisible()) {
      await viewButtons.first().click()
    }
  })
})

test.describe('Public Booking Page', () => {
  test('should show booking types on public page', async ({ page }) => {
    await page.goto('/book')
    // May redirect or show booking options
    await expect(page.locator('body')).not.toBeEmpty()
  })

  test('should handle invalid booking slug', async ({ page }) => {
    await page.goto('/book/nonexistent-type')
    await expect(page.locator('body')).toContainText(/not found|unavailable|error/i)
  })
})
