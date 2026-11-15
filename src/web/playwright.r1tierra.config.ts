// asistido por SI: Claude Code (Anthropic), E2E de Earth (W2) sobre el build de R1 en su propio puerto (C-F3-15)
import { defineConfig, devices } from '@playwright/test'

// Antes: npm run build y python -m mapa_estatico.construir --desplegar src/web/dist (con AGROVERSEX_DATOS)
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: 'build_tierra_fase3.spec.ts', timeout: 90_000, workers: 1, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5331', port: 5331, reuseExistingServer: false },
  use: { baseURL: 'http://localhost:5331', headless: true, viewport: { width: 1440, height: 900 } },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: { width: 1440, height: 900 } } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: { width: 1440, height: 900 } } },
  ],
})
