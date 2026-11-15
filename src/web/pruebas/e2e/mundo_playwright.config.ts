// asistido por SI: Claude Code (Anthropic), E2E de las series del mundo sobre dist desplegado, en Chromium, Firefox y WebKit (S1w)
import { defineConfig, devices } from '@playwright/test'

// Antes: npm run build y python -m mapa_estatico.construir --desplegar src/web/dist (con AGROVERSEX_DATOS)
const reducido = process.env.MUNDO_REDUCIDO === '1'
export default defineConfig({
  testDir: '.', testMatch: 'mundo_tierra.spec.ts', timeout: 150_000, workers: 1, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5320', port: 5320, reuseExistingServer: false, cwd: '../..' },
  use: { baseURL: 'http://localhost:5320', headless: true, viewport: { width: 1440, height: 900 }, ...(reducido ? { reducedMotion: 'reduce' as const } : {}) },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: { width: 1440, height: 900 } } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: { width: 1440, height: 900 } } },
  ],
})
