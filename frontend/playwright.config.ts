import { defineConfig } from '@playwright/test'

declare const process: { env: Record<string, string | undefined> }

// Business-loop e2e targets the BACKEND same-origin on :8000: main.py serves the
// built frontend/dist AND the /api routes, so no vite preview / proxy is needed.
// Run `npm run build` (or scripts/test-e2e.ps1) before `npm run test:e2e`.
const backendPort = 8000
const browserExecutable = process.env.PAWTWIN_BROWSER_EXECUTABLE

export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results',
  fullyParallel: false,
  retries: 0,
  reporter: 'line',
  use: {
    baseURL: `http://127.0.0.1:${backendPort}`,
    launchOptions: browserExecutable ? { executablePath: browserExecutable } : undefined,
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `uv run --project .. --frozen uvicorn pawtwin.main:create_app --factory --host 127.0.0.1 --port ${backendPort}`,
      url: `http://127.0.0.1:${backendPort}/healthz`,
      env: { PAWTWIN_MODE: 'local' },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
