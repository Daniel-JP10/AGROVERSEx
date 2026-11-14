// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Medición de la PoC de recoloreo ADM2. Variables: VARIANTES=A,B,C  RANURA=2000  VALIDAR=0  ETIQUETA=x  CARGA=texto
import { test, expect } from '@playwright/test'
import fs from 'node:fs'

const VARIANTES = (process.env.VARIANTES || 'A,B,C').split(',')
const RANURA = process.env.RANURA || '2000'
const VALIDAR = process.env.VALIDAR || '0'
const ETIQ = process.env.ETIQUETA || 'corrida'
const VISTAS = [
  { n: 'colombia-z6', lat: 4.5, lng: -74, z: 6 }, { n: 'colombia-z7', lat: 4.5, lng: -74, z: 7 },
  { n: 'india-z6', lat: 22, lng: 79, z: 6 }, { n: 'india-z7', lat: 22, lng: 79, z: 7 },
  { n: 'europa-z6', lat: 48, lng: 10, z: 6 }, { n: 'europa-z7', lat: 48, lng: 10, z: 7 },
]
const SALIDA = `capturas/poc-resultados-${ETIQ}.json`
const pct = (a: number[], p: number) => { const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))] }

fs.mkdirSync('capturas', { recursive: true })
// cada test corre en su propio proceso si uno falla: se acumula leyendo el archivo
const leer = (): any[] => (fs.existsSync(SALIDA) ? JSON.parse(fs.readFileSync(SALIDA, 'utf8')) : [])

for (const v of VARIANTES) for (const vista of VISTAS) {
  test(`${v} ${vista.n}`, async ({ page }) => {
    const cdp = await page.context().newCDPSession(page)
    await cdp.send('Performance.enable')
    await page.goto(`/pruebas/poc/adm2.html?auto=0&v=${v}&lat=${vista.lat}&lng=${vista.lng}&z=${vista.z}&n=${RANURA}&val=${VALIDAR}`)
    await page.waitForFunction(() => (window as any).pocListo)
    await page.evaluate(async () => {
      const w = window as any
      w.ids = await w.poc.cargarIds()
      if (!w.poc.mapa.areTilesLoaded()) await new Promise((r) => w.poc.mapa.once('idle', r))
    })
    // Mes completo con el mapa quieto (mapa de tres meses para calentar)
    const quieto: number[] = await page.evaluate(async (v) => {
      const w = window as any, out: number[] = []
      for (let mes = 0; mes < 6; mes++) {
        const r = await w.poc.aplicarMes(v, mes, w.poc.valoresDelMes(w.ids.length, mes), w.ids)
        if (mes > 0) out.push(r.ms) // el primero incluye calentamiento
        await new Promise((r) => setTimeout(r, 60))
      }
      return out
    }, v)

    const m0 = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map((x) => [x.name, x.value]))
    const r = await page.evaluate(async (v) => {
      const w = window as any, mapa = w.poc.mapa
      const dts: number[] = [], largas: number[] = [], mesesMs: number[] = []
      let renders = 0, superadas = 0, fase = 0, mes = 6
      mapa.on('render', () => renders++)
      new PerformanceObserver((l) => l.getEntries().forEach((e) => largas.push(e.duration))).observe({ entryTypes: ['longtask'] })
      let interaccion = 0 // eventos reales de usuario durante la medición (contaminan)
      for (const e of ['mousedown', 'wheel', 'keydown', 'touchstart']) addEventListener(e, () => interaccion++, true)
      let oculto = 0
      const foco0 = [document.hasFocus(), document.visibilityState]
      document.addEventListener('visibilitychange', () => oculto++)
      const t0 = performance.now()
      let ult = t0, ultMes = t0
      await new Promise<void>((fin) => {
        const f = (t: number) => {
          dts.push(t - ult); ult = t
          fase += 0.07
          mapa.panBy([7 * Math.cos(fase), 4 * Math.sin(fase * 0.7)], { animate: false })
          if (t - ultMes >= 250) { // 4 meses por segundo
            ultMes = t
            const m = ++mes
            w.poc.aplicarMes(v, m, w.poc.valoresDelMes(w.ids.length, m), w.ids).then((x: any) => (x.ms < 0 ? superadas++ : mesesMs.push(x.ms)))
          }
          t - t0 < 10000 ? requestAnimationFrame(f) : fin()
        }
        requestAnimationFrame(f)
      })
      dts.shift()
      // el mapa debe estar realmente recoloreado: valores distintos entre unidades visibles
      const vals = new Set<number>(), vis = mapa.querySourceFeatures('adm2', { sourceLayer: 'adm2' })
      if (v === 'C') vals.add(Array.isArray(mapa.getPaintProperty('adm2-relleno', 'fill-color')) ? 1 : 0)
      else for (const f of vis) vals.add(+(mapa.getFeatureState({ source: 'adm2', sourceLayer: 'adm2', id: f.properties.id }) as any).v)
      return { dts, largas, mesesMs, renders, superadas, interaccion, oculto, foco0, distintos: vals.size, visibles: vis.length }
    }, v)
    const m1 = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map((x) => [x.name, x.value]))
    await page.screenshot({ path: `capturas/poc-${ETIQ}-${v}-${vista.n}.png` })

    const frames = r.dts.length
    const cpuMs = ((m1.TaskDuration - m0.TaskDuration) * 1000) / frames
    const fila = {
      etiqueta: ETIQ, variante: v, vista: vista.n, ranura: RANURA, validar: VALIDAR, frames,
      fps: +(frames / (r.dts.reduce((a, b) => a + b, 0) / 1000)).toFixed(1),
      p95: +pct(r.dts, 0.95).toFixed(1), max: +Math.max(...r.dts).toFixed(1),
      cpuPorFrame: +cpuMs.toFixed(2), scriptPorFrame: +(((m1.ScriptDuration - m0.ScriptDuration) * 1000) / frames).toFixed(2),
      longtasks: r.largas.length, longtaskMax: r.largas.length ? +Math.max(...r.largas).toFixed(0) : 0,
      rendersPorSeg: +(r.renders / 10).toFixed(1),
      mesQuietoMax: +Math.max(...quieto).toFixed(0), mesQuietoMed: +pct(quieto, 0.5).toFixed(0),
      mesEnCursoMax: r.mesesMs.length ? +Math.max(...r.mesesMs).toFixed(0) : null, interaccion: r.interaccion, foco: r.foco0.join('/'), oculto: r.oculto, distintos: r.distintos, visibles: r.visibles, mesesSuperados: r.superadas, mesesCompletos: r.mesesMs.length,
    }
    fs.writeFileSync(SALIDA, JSON.stringify([...leer(), fila], null, 1))
    console.log(JSON.stringify(fila))

    expect(fila.distintos, 'la vista debe estar recoloreada').toBeGreaterThan(v === 'C' ? 0 : 20)
    if (v === 'A') return // referencia, se espera que falle
    // Criterio vinculante: no se relaja
    expect(fila.fps, 'fps promedio').toBeGreaterThanOrEqual(58)
    expect(fila.p95, 'p95 ms').toBeLessThanOrEqual(20)
    expect(fila.max, 'frame máximo ms').toBeLessThanOrEqual(50)
    expect(fila.mesQuietoMax, 'mes completo (quieto) ms').toBeLessThanOrEqual(250)
    expect(fila.mesEnCursoMax ?? 1e9, 'mes completo (en paneo) ms').toBeLessThanOrEqual(250)
    expect(fila.mesesSuperados, 'meses no terminados a tiempo').toBe(0)
  })
}
