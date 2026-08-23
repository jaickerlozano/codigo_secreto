import { existsSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'

import { defineConfig } from '@playwright/test'

// Real-browser acceptance harness for the checkout Radix owned-scroll
// scenario that jsdom cannot compute (layout). Runs the real Vite dev
// server; backend/network dependencies are mocked per-test at the browser
// boundary via page.route, so no backend or credentials are required.
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  // Single worker keeps the acceptance evidence deterministic on low-RAM hosts.
  workers: 1,
  reporter: 'list',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: 'http://localhost:5173',
    // Constrained mobile viewport: the acceptance requires the option list to
    // exceed the available height (owned scroll).
    viewport: { width: 390, height: 700 },
    trace: 'retain-on-failure',
    launchOptions: {
      // Dev host without system browser deps: use user-local shared libs
      // when present; machines with system deps are unaffected.
      env: {
        ...process.env,
        ...(existsSync(join(homedir(), '.local/share/playwright-libs'))
          ? {
              LD_LIBRARY_PATH: join(homedir(), '.local/share/playwright-libs'),
            }
          : {}),
      },
      // The stripped headless shell crashes while rendering this app on
      // low-RAM hosts; the full chromium build in new-headless mode is
      // stable. Software rasterization is disabled for the same reason.
      args: ['--disable-gpu', '--disable-software-rasterizer'],
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium', channel: 'chromium' },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
