// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Corrida única: capturas de atmósfera/fondo y fps de paneo. Uso: node pruebas/e2e/captura.mjs (con vite en 5199)
import { chromium } from '@playwright/test'

const b = await chromium.launch({ channel: 'chrome', headless: false, args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization'] })
const p = await b.newPage({ viewport: { width: 1400, height: 850 } })
const malas = []
p.on('response', (r) => { if (r.url().includes('gibs.earthdata.nasa.gov') && r.status() >= 400) malas.push(r.status() + ' ' + r.url()) })
await p.goto('http://localhost:5199/')
await p.waitForFunction(() => window.__mapa && window.__mapa.loaded(), null, { timeout: 60000 })
const ir = async (z, c) => { await p.evaluate(([z, c]) => window.__mapa.jumpTo({ zoom: z, center: c }), [z, c]); await p.waitForTimeout(4000) }
await ir(1.6, [-60, 10]); await p.screenshot({ path: 'capturas/08-atmosfera-z1.png' })
await ir(3, [-74, 4]); await p.screenshot({ path: 'capturas/08-atmosfera-z3.png' })
await ir(10, [-73, 3.5]); await p.screenshot({ path: 'capturas/07-fondo-z10-despues.png' })
// paneo 5 s a zoom 5 (fondo de detalle ya visible), fps por requestAnimationFrame
const r = await p.evaluate(async () => {
  const m = window.__mapa; m.jumpTo({ zoom: 5, center: [-74, 4] })
  const dts = []; let t0 = performance.now(), x = 0
  await new Promise((ok) => { const f = (t) => { dts.push(t - t0); t0 = t; m.panBy([x++ % 2 ? 6 : -6, 2], { duration: 0 }); if (dts.length < 300) requestAnimationFrame(f); else ok() }; requestAnimationFrame(f) })
  dts.shift(); dts.sort((a, b) => a - b)
  return { fps: +(1000 / (dts.reduce((a, c) => a + c, 0) / dts.length)).toFixed(1), p95: dts[Math.floor(dts.length * 0.95)], max: dts.at(-1) }
})
console.log(JSON.stringify({ ...r, errores_gibs: malas }))
await b.close()
