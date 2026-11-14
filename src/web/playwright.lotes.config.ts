// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { defineConfig } from '@playwright/test'

const D = decodeURIComponent(new URL('../../datos/procesados', import.meta.url).pathname).replace(/^\/(\w:)/, '$1')
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: 'lotes.spec.ts', timeout: 90_000, workers: 1, reporter: 'list',
  webServer: { command: 'npx vite --port 5316 --strictPort', port: 5316, reuseExistingServer: false, env: { AGROVERSEX_DATOS: D, AGROVERSEX_SQLITE: `${D}/agroversex.sqlite` } },
  use: { baseURL: 'http://localhost:5316', channel: 'chrome', headless: false, viewport: { width: 1400, height: 850 } },
})
