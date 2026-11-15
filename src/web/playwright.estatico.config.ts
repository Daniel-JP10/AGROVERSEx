// asistido por SI: Claude Code (Anthropic), E2E sobre el build estático servido sin Vite ni API (D-037 C2)
import { defineConfig } from '@playwright/test'

// Antes: npm run build y python -m mapa_estatico.construir --desplegar src/web/dist (con AGROVERSEX_DATOS)
export default defineConfig({
  testDir: 'pruebas/e2e', testMatch: 'build_*.spec.ts', timeout: 90_000, workers: 1, reporter: 'list',
  webServer: { command: 'node pruebas/build_servidor.mjs dist 5198', port: 5198, reuseExistingServer: false },
  use: { baseURL: 'http://localhost:5198', channel: 'chrome', headless: true, viewport: { width: 1400, height: 850 } },
})
