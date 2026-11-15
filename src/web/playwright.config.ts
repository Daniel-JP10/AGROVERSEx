// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { defineConfig } from '@playwright/test'

// Solo para la PoC de rendimiento: Chrome real, ventana visible para usar la GPU
export default defineConfig({
  testDir: 'pruebas/poc', testMatch: '*.spec.ts', timeout: 900_000, workers: 1, reporter: 'list',
  webServer: [
    { command: 'node pruebas/poc/servidor.mjs', port: 5198, reuseExistingServer: false },
    { command: 'npx vite --port 5199 --strictPort', port: 5199, reuseExistingServer: false },
  ],
  use: {
    baseURL: 'http://localhost:5199', channel: 'chrome', headless: false, viewport: { width: 1400, height: 850 },
    launchOptions: { args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--disable-backgrounding-occluded-windows', '--disable-renderer-backgrounding', '--disable-background-timer-throttling'] },
  },
})
