// asistido por SI: Claude Code (Anthropic), E2E del marco y las pantallas de W1 sobre el build estático en Chromium, Firefox y WebKit
import { defineConfig, devices } from '@playwright/test'

// Antes: npx vite build (dist/). El servidor solo sirve archivos, como el alojamiento estático
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: /(marco|portada|ciencia|datos_abiertos|fuentes)_.*\.spec\.ts$/, timeout: 60_000, workers: 3, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5199', port: 5199, reuseExistingServer: false },
  use: { baseURL: 'http://localhost:5199', headless: true, viewport: { width: 1440, height: 900 } },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: { width: 1440, height: 900 } } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: { width: 1440, height: 900 } } },
  ],
})
