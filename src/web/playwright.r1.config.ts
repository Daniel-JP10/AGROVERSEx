// asistido por SI: Claude Code (Anthropic), E2E del marco y la entrada de R1 en su propio puerto (C-F3-15)
import { defineConfig, devices } from '@playwright/test'

// Sembrado de idioma con el origen de este puerto (marco_ayuda.ts)
process.env.E2E_ORIGEN = 'http://localhost:5330'

// Antes: npx vite build (dist/). El servidor solo sirve archivos, como el alojamiento estático
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: /(marco|portada|ciencia|datos_abiertos|fuentes)_.*\.spec\.ts$/, timeout: 60_000, workers: 3, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5330', port: 5330, reuseExistingServer: false },
  use: { baseURL: 'http://localhost:5330', headless: true, viewport: { width: 1440, height: 900 } },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: { width: 1440, height: 900 } } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: { width: 1440, height: 900 } } },
  ],
})
