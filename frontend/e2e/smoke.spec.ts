import { expect, test } from '@playwright/test'

test('core routes render', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText(/Explore TB futures/i)).toBeVisible()
  await page.goto('/prioritization')
  await expect(page.getByText(/Find where BCG scale-up matters most/i)).toBeVisible()
  await page.goto('/map')
  await expect(page.getByText(/Map burden, prevention, and system context/i)).toBeVisible()
  await page.goto('/model')
  await expect(page.getByText(/Inspect the model without losing the product feel/i)).toBeVisible()
})
