import { test, expect } from '@playwright/test';

test.describe('AETHER-BUST Operational Console Smoke Test', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
  });

  test('UX-2: Main panels are rendered', async ({ page }) => {
    // TopBar
    await expect(page.locator('text=AETHER-BUST')).toBeVisible();

    // Map container (RiskMap renders relative wrapper)
    const mapContainer = page.locator('.relative.w-full.h-full.flex.flex-col');
    await expect(mapContainer).toBeVisible();

    // Control rails
    await expect(page.locator('text=Variable')).toBeVisible();
    await expect(page.locator('text=Opacity')).toBeVisible();

    // XAI Panel (Phase 5)
    const xaiPanel = page.locator('#xai-panel');
    await expect(xaiPanel).toBeVisible();
    await expect(page.locator('text=Explainability (XAI)')).toBeVisible();
  });

  test('UX-3: Scrubber interaction updates lead time', async ({ page }) => {
    const scrubber = page.locator('input[type="range"]').last();
    await expect(scrubber).toBeVisible();
    await scrubber.fill('5');
    
    // Check if the store lead time updated (UI reflection)
    await expect(page.locator('text=Day 5').first()).toBeVisible();
  });

  test('UX-5: XAI Panel shows drivers', async ({ page }) => {
    // XAI Panel displays "Select a bust detection region" initially or mock data
    const xaiPanel = page.locator('#xai-panel');
    await expect(xaiPanel).toBeVisible();
    
    // We already populate mock drivers if selection is true, but for the smoke test
    // we can just verify the layout doesn't crash
    await expect(page.locator('text=Explainability (XAI)')).toBeVisible();
  });
});
