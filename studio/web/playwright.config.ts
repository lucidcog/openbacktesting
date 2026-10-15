import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
export default defineConfig({
  testDir: './e2e', testMatch: '**/*.spec.ts', fullyParallel: false,
  workers: 1, retries: 0, timeout: 90_000, expect: { timeout: 15_000 },
  outputDir: resolve(process.env.HARNESS_EVIDENCE_DIR ?? '../../.verification/browser', 'browser'),
  reporter: [['list'], ['./e2e/evidence-reporter.ts']],
  use: { actionTimeout: 15_000, navigationTimeout: 15_000, browserName: 'chromium', headless: true, viewport: { width: 1440, height: 1000 },
    trace: 'off', screenshot: 'off', video: 'off', serviceWorkers: 'block' },
})
