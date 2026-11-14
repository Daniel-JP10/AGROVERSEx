// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { defineConfig } from '@playwright/test'

// E2E de búsqueda/miga: usa geo.sqlite (tabla unidad con bbox) si agroversex.sqlite aún no existe
const D = decodeURIComponent(new URL('../../datos/procesados', import.meta.url).pathname).replace(/^\/(\w:)/, '$1')
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: 'busqueda.spec.ts', timeout: 90_000, workers: 1, reporter: 'list',
  webServer: { command: 'npx vite --port 5198 --strictPort', port: 5198, reuseExistingServer: false, env: { AGROVERSEX_DATOS: D, AGROVERSEX_SQLITE: `${D}/geo.sqlite` } },
  use: { baseURL: 'http://localhost:5198', channel: 'chrome', headless: false, viewport: { width: 1400, height: 850 } },
})
