import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: 'https://quest-kit.vercel.app',
    trace: 'on-first-retry',
  },
});
