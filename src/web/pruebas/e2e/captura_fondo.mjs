// asistido por SI: Claude Code, captura de Colombia con el fondo GIBS y vigilancia de errores 4xx
// Uso: node pruebas/e2e/captura_fondo.mjs (con vite en 5199)
import { chromium } from '@playwright/test'

const b = await chromium.launch({ channel: 'chrome', headless: true, args: ['--ignore-gpu-blocklist', '--use-gl=swiftshader'] })
const p = await b.newPage({ viewport: { width: 1400, height: 850 } })
const malas = []; let gibs = 0; const capas = new Set()
p.on('response', (r) => { if (r.url().includes('gibs.earthdata.nasa.gov')) { gibs++; capas.add(r.url().split('/')[6]); if (r.status() >= 400) malas.push(r.status() + ' ' + r.url()) } })
await p.goto('http://localhost:5199/')
await p.waitForFunction(() => window.__mapa && window.__mapa.loaded(), null, { timeout: 60000 })
const ir = async (z, c, f) => { await p.evaluate(([z, c]) => window.__mapa.jumpTo({ zoom: z, center: c }), [z, c]); await p.waitForTimeout(6000); await p.screenshot({ path: f }) }
await ir(5, [-74, 4.5], '../../datos/evidencia/gibs_colombia_z5.png')
await ir(7.5, [-77.6, 1.3], '../../datos/evidencia/gibs_narino_z7.png')
console.log(JSON.stringify({ teselas_gibs: gibs, capas: [...capas], errores_gibs: malas }))
await b.close()
