// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { apiLocal } from './server/api'
import { servirTeselas } from './server/teselas'

// Ruta de la base: AGROVERSEX_SQLITE si existe, si no la definitiva de datos/procesados
const rutaDb = process.env.AGROVERSEX_SQLITE ?? decodeURIComponent(new URL('../../datos/procesados/agroversex.sqlite', import.meta.url).pathname).replace(/^\/(\w:)/, '$1')

export default defineConfig({
  plugins: [react(), apiLocal({ rutaDb }), servirTeselas()],
  build: { chunkSizeWarningLimit: 1500 }, // MapLibre pesa ~1 MB sin comprimir
  test: { include: ['pruebas/**/*.test.ts'] },
})
