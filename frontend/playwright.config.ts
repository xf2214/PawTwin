import { defineConfig } from '@playwright/test'

declare const process: { env: Record<string, string | undefined> }

const backendPort = 8000
const frontendPort = Number(process.env.PAWTWIN_E2E_PORT ?? 4173)
const browserExecutable = process.env.PAWTWIN_BROWSER_EXECUTABLE

export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results',
  fullyParallel: false,
  retries: 0,
  reporter: 'line',
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
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
    {
      command: `npm run preview -- --host 127.0.0.1 --port ${frontendPort} --strictPort`,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
