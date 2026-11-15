// asistido por SI: Claude Code (Anthropic), E2E de El lote y Rotaciones sobre el build estático en Chromium, Firefox y WebKit
import { defineConfig, devices } from '@playwright/test'

// Antes: npm run build (dist trae public/gemelo y public/lotes)
const vista = { width: 1440, height: 900 }
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: 'lote_*.spec.ts', timeout: 60_000, workers: 1, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5213', port: 5213, reuseExistingServer: false },
  use: { baseURL: 'http://localhost:5213', headless: true, viewport: vista },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: vista } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: vista } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: vista } },
  ],
})
