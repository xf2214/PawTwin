import { defineConfig } from '@playwright/test'

declare const process: { env: Record<string, string | undefined> }

// Business-loop e2e targets the BACKEND same-origin on :8000: main.py serves the
// built frontend/dist AND the /api routes, so no vite preview / proxy is needed.
// Run `npm run build` (or scripts/test-e2e.ps1) before `npm run test:e2e`.
const backendPort = Number(process.env.PAWTWIN_E2E_PORT ?? '8000')
if (!Number.isInteger(backendPort) || backendPort < 1024 || backendPort > 65535) {
  throw new Error('PAWTWIN_E2E_PORT must be a port from 1024 to 65535')
}
const browserExecutable = process.env.PAWTWIN_BROWSER_EXECUTABLE
const recordDemo = process.env.PAWTWIN_RECORD_DEMO === '1'

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
    // Existing business scenarios use Chinese; i18n.spec overrides with clean
    // storage to exercise the production English default. Secondary visitor
    // contexts explicitly choose Chinese in their scenario setup.
    storageState: { cookies: [], origins: [{ origin: `http://127.0.0.1:${backendPort}`, localStorage: [{ name: 'pawtwin-language', value: 'zh' }] }] },
    launchOptions: browserExecutable ? { executablePath: browserExecutable } : undefined,
    trace: 'retain-on-failure',
    video: recordDemo ? { mode: 'on', size: { width: 1280, height: 800 } } : 'off',
    viewport: { width: 1280, height: 800 },
  },
  webServer: [
    {
      command: `uv run --project .. --frozen uvicorn pawtwin.main:create_app --factory --host 127.0.0.1 --port ${backendPort} --no-proxy-headers`,
      url: `http://127.0.0.1:${backendPort}/healthz`,
      env: {
        PAWTWIN_MODE: 'local',
        // Exercise the SHIPPED asynchronous path, not the inline test default.
        PAWTWIN_WORKER_MODE: 'background',
        // The labelled stand-in: no AWS account is available, and nothing here
        // may be mistaken for a real model call.
        PAWTWIN_MODEL_BACKEND: 'local_fake',
        // Never inherit a user's persistent preview database or cloud settings.
        PAWTWIN_DB_PATH: ':memory:',
        PAWTWIN_MEMORY_BACKEND: 'not_implemented',
        PAWTWIN_PHOTO_RECOGNITION_ENABLED: 'false',
        PAWTWIN_FAMILY_MODEL_BACKEND: 'local_rules',
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
