// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { defineConfig } from '@playwright/test'

// E2E de la interfaz: Chrome real, un solo worker
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: '*.spec.ts', timeout: 60_000, workers: 1, reporter: 'list',
  webServer: { command: 'npx vite --port 5197 --strictPort', port: 5197, reuseExistingServer: false },
  use: { baseURL: 'http://localhost:5197', channel: 'chrome', headless: false, viewport: { width: 1400, height: 850 } },
})
