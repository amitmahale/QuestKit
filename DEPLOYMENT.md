# Deployment and e2e test steps

## 1) Install plugin / tooling

```bash
npx plugins add vercel/vercel-plugin
```

## 2) Deploy to Vercel

```bash
npx vercel --prod --yes
```

Expected production URL target:

- `https://quest-kit.vercel.app`

## 3) Playwright test against production

```bash
npm install
npx playwright install --with-deps
npx playwright test
```

The e2e test is configured in `e2e/quest-kit.spec.ts` and targets `https://quest-kit.vercel.app` via `playwright.config.ts`.
