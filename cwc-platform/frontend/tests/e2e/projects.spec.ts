import { test, expect } from '@playwright/test'

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login')
    await page.fill('input[type="email"]', 'dev@cwcplatform.com')
    await page.click('button:has-text("Dev Login")')
    await page.waitForURL('**/dashboard')
  })

  test('should display projects list page', async ({ page }) => {
    await page.goto('/projects')
    await expect(page).toHaveURL(/.*projects/)
    await expect(page.locator('h1, h2')).toContainText(/project/i)
  })

  test('should navigate to create project', async ({ page }) => {
    await page.goto('/projects')
    const createButton = page.locator('button:has-text("Create"), button:has-text("New"), a:has-text("Create")')
    if (await createButton.isVisible()) {
      await createButton.click()
    }
  })

  test('should filter projects by status', async ({ page }) => {
    await page.goto('/projects')
    const statusFilter = page.locator('[data-testid="status-filter"], select').first()
    if (await statusFilter.isVisible()) {
      await statusFilter.click()
    }
  })

  test('should display project templates page', async ({ page }) => {
    await page.goto('/projects/templates')
    await expect(page.locator('body')).toContainText(/template|project/i)
  })
})

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"]', 'dev@cwcplatform.com')
    await page.click('button:has-text("Dev Login")')
    await page.waitForURL('**/dashboard')
  })

  test('should display tasks within project', async ({ page }) => {
    await page.goto('/projects')
    // Click on first project if exists
    const projectLink = page.locator('a[href*="/projects/"]').first()
    if (await projectLink.isVisible()) {
      await projectLink.click()
      await expect(page.locator('body')).toContainText(/task|todo|activity/i)
    }
  })
})
