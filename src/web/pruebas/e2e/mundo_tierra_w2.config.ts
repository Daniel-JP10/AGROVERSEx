// asistido por SI: Claude Code (Anthropic), copia del config E2E de Earth de W2 sobre el dist del mundo, puerto 5321 propio (S1w)
import { defineConfig, devices } from '@playwright/test'

// Antes: npm run build y python -m mapa_estatico.construir --desplegar src/web/dist (con AGROVERSEX_DATOS)
export default defineConfig({
  testDir: '.', testMatch: 'build_tierra_fase3.spec.ts', timeout: 90_000, workers: 1, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5321', port: 5321, reuseExistingServer: false, cwd: '../..' },
  use: { baseURL: 'http://localhost:5321', headless: true, viewport: { width: 1440, height: 900 } },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: { width: 1440, height: 900 } } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: { width: 1440, height: 900 } } },
  ],
})
