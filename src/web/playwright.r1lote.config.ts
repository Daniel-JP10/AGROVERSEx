// asistido por SI: Claude Code (Anthropic), E2E del lote de R1 en su propio puerto (C-F3-15)
import { defineConfig, devices } from '@playwright/test'

process.env.E2E_ORIGEN = 'http://localhost:5334'

// Antes: npm run build (dist trae public/gemelo y public/lotes)
const vista = { width: 1440, height: 900 }
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: 'lote_*.spec.ts', timeout: 60_000, workers: 1, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5334', port: 5334, reuseExistingServer: false },
  use: { baseURL: 'http://localhost:5334', headless: true, viewport: vista },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: vista } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: vista } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: vista } },
  ],
})
