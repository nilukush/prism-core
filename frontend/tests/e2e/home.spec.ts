import { test, expect } from '@playwright/test'

test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display the home page', async ({ page }) => {
    // Check if the page title is correct
    await expect(page).toHaveTitle(/PRISM/)
    
    // Check if main heading is visible
    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()
  })

  test('should navigate to login page', async ({ page }) => {
    // Click on login link/button
    const loginLink = page.getByRole('link', { name: /sign in/i })
    await expect(loginLink).toBeVisible()
    await loginLink.click()
    
    // Verify navigation to login page
    await expect(page).toHaveURL('/auth/login')
  })

  test('should display main features', async ({ page }) => {
    // Check for feature sections
    const features = page.getByTestId('features-section')
    await expect(features).toBeVisible()
    
    // Verify key features are mentioned
    await expect(page.getByText(/AI-Powered/i)).toBeVisible()
    await expect(page.getByText(/Product Management/i)).toBeVisible()
  })

  test('should have responsive design', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 })
    const desktopNav = page.getByTestId('desktop-nav')
    await expect(desktopNav).toBeVisible()
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 })
    const mobileMenuButton = page.getByTestId('mobile-menu-button')
    await expect(mobileMenuButton).toBeVisible()
  })

  test('should have proper meta tags for SEO', async ({ page }) => {
    // Check meta description
    const metaDescription = page.locator('meta[name="description"]')
    await expect(metaDescription).toHaveAttribute('content', /PRISM.*Product.*Management/i)
    
    // Check Open Graph tags
    const ogTitle = page.locator('meta[property="og:title"]')
    await expect(ogTitle).toHaveAttribute('content', /PRISM/i)
  })
})