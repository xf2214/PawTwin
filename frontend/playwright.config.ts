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
  // ONE worker on purpose: every spec shares a single server process and a single
  // in-memory SQLite database, so parallel files would inject facts and simulated
  // device modes into each other's runs.
  workers: 1,
  // Retries stay at 0: a retry would hide a real race behind an occasional green.
  retries: 0,
  reporter: 'line',
  expect: {
    // Analysis is asynchronous, so an assertion must be allowed to watch
    // queued -> analyzing -> awaiting_approval. Playwright's 5s default is not.
    timeout: 20_000,
  },
  use: {
    baseURL: `http://127.0.0.1:${backendPort}`,
    launchOptions: browserExecutable ? { executablePath: browserExecutable } : undefined,
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `uv run --project .. --frozen uvicorn pawtwin.main:create_app --factory --host 127.0.0.1 --port ${backendPort}`,
      url: `http://127.0.0.1:${backendPort}/healthz`,
      env: {
        PAWTWIN_MODE: 'local',
        // Exercise the SHIPPED asynchronous path, not the inline test default.
        PAWTWIN_WORKER_MODE: 'background',
        // The labelled stand-in: no AWS account is available, and nothing here
        // may be mistaken for a real model call.
        PAWTWIN_MODEL_BACKEND: 'local_fake',
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
