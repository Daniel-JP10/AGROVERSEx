// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { defineConfig } from '@playwright/test'

// Medición sobre la app real (Vite con API y teselas). Datos por ruta absoluta, sin copiar.
const D = decodeURIComponent(new URL('../../datos/procesados', import.meta.url).pathname).replace(/^\/(\w:)/, '$1')
export default defineConfig({
  testDir: 'pruebas/poc', testMatch: 'medirapp.spec.ts', timeout: 900_000, workers: 1, reporter: 'list', retries: 0,
  webServer: {
    command: 'npx vite preview --port 5201 --strictPort', port: 5201, reuseExistingServer: false,
    env: { AGROVERSEX_DATOS: D, AGROVERSEX_SQLITE: `${D}/agroversex.sqlite` },
  },
  use: {
    baseURL: 'http://localhost:5201', channel: 'chrome', headless: false, viewport: { width: 1400, height: 850 },
    launchOptions: { args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--disable-backgrounding-occluded-windows', '--disable-renderer-backgrounding', '--disable-background-timer-throttling'] },
  },
})
