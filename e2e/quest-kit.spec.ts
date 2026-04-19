import { test, expect } from '@playwright/test';

test('homepage renders expected QuestKit MVP content', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /turn curiosity into play/i })).toBeVisible();
  await expect(page.getByText(/Playable Modes/i)).toBeVisible();
  await expect(page.getByText(/Quick Quiz/i)).toBeVisible();
  await expect(page.getByText(/Chapter-to-Game/i)).toBeVisible();
});
