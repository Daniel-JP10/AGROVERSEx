// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Medición de B con recoloreo diferido (D-015) sobre el build. Variable: ETIQUETA
import { test, expect } from '@playwright/test'
import fs from 'node:fs'

const ETIQ = process.env.ETIQUETA || 'app'
const VISTAS = [
  { n: 'colombia-z6', lat: 4.5, lng: -74, z: 6 }, { n: 'colombia-z7', lat: 4.5, lng: -74, z: 7 },
  { n: 'india-z6', lat: 22, lng: 79, z: 6 }, { n: 'india-z7', lat: 22, lng: 79, z: 7 },
  { n: 'europa-z6', lat: 48, lng: 10, z: 6 }, { n: 'europa-z7', lat: 48, lng: 10, z: 7 },
  { n: 'paris-z11', lat: 48.86, lng: 2.35, z: 11 }, { n: 'iowa-z11', lat: 42, lng: -93.5, z: 11 }, { n: 'nairobi-z11', lat: -1.29, lng: 36.82, z: 11 },
]
const SALIDA = `capturas/app-resultados-${ETIQ}.json`
const pct = (a: number[], p: number) => { const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))] }
fs.mkdirSync('capturas', { recursive: true })
const leer = (): unknown[] => (fs.existsSync(SALIDA) ? JSON.parse(fs.readFileSync(SALIDA, 'utf8')) : [])

for (const vista of VISTAS) {
  test(`app B ${vista.n}`, async ({ page }) => {
    const cdp = await page.context().newCDPSession(page)
    await cdp.send('Performance.enable')
    await page.goto('/')
    await page.waitForFunction(() => (window as any).__mapa?.loaded())
    await page.evaluate(({ lat, lng, z }) => { (window as any).__mapa.jumpTo({ center: [lng, lat], zoom: z, pitch: 0, bearing: 0 }) }, vista)
    await page.evaluate(() => new Promise((r) => (window as any).__mapa.once('idle', r)))
    await page.waitForTimeout(1500)
    const fm = () => cdp.send('Performance.getMetrics').then((x) => Object.fromEntries(x.metrics.map((y) => [y.name, y.value])))
    await page.getByRole('button', { name: 'Reproducir' }).click() // 4 meses/s
    await page.evaluate(() => {
      // copia de src/tiempo/valor.ts (en el build de producción no se puede importar el módulo)
      const hash01 = (id: string) => { let h = 0x811c9dc5; for (const ch of id) { h ^= ch.charCodeAt(0); h = Math.imul(h, 0x01000193) } return (h >>> 0) / 4294967296 }
      const valor = (id: string, mes: number) => { const base = hash01(id), fase = hash01(`${id}:f`) * 2 * Math.PI; return Math.min(1, Math.max(0, 0.5 + 0.5 * (base - 0.5) + 0.22 * Math.sin((2 * Math.PI * mes) / 12 + fase) + 0.12 * Math.sin((2 * Math.PI * mes) / (60 + 40 * base) + fase))) }
      const w = window as any, mapa = w.__mapa
      w.mesActual = () => +(document.querySelector('input[aria-label="Mes"]') as HTMLInputElement).value
      w.fuenteActiva = () => (mapa.getZoom() >= 7 ? 'adm2' : 'adm1') // nivel que se colorea (D-015)
      // true si todo lo cargado del nivel activo lleva el mes dado
      w.completo = (mes: number) => {
        const f = w.fuenteActiva(), vistos = new Set<string>()
        for (const x of mapa.querySourceFeatures(f, { sourceLayer: f })) {
          const id = x.properties.id
          if (vistos.has(id)) continue
          vistos.add(id)
          if (mapa.getFeatureState({ source: f, sourceLayer: f, id }).v !== valor(id, mes)) return false
        }
        return true
      }
      w.distintos = () => {
        const f = w.fuenteActiva(), v = new Set<number>(); let sin = 0
        for (const x of mapa.querySourceFeatures(f, { sourceLayer: f })) { const e = mapa.getFeatureState({ source: f, sourceLayer: f, id: x.properties.id }).v; e === undefined ? sin++ : v.add(+e) }
        return { distintos: v.size, sinEstado: sin }
      }
    })

    // Fase 1: gesto de arrastre continuo (mouse sintético) con reproducción; los frames se miden sin comprobaciones
    const m0 = await fm()
    const r = await page.evaluate(async () => {
      const w = window as any, mapa = w.__mapa, cv = mapa.getCanvas()
      const dts: number[] = [], largas: [number, number][] = [], teselas: number[] = [], inter = { n: 0 }
      for (const e of ['wheel', 'keydown']) addEventListener(e, () => inter.n++, true)
      mapa.on('sourcedata', (e: any) => { if (e.tile) teselas.push(performance.now()) })
      new PerformanceObserver((l) => l.getEntries().forEach((e) => largas.push([e.startTime, e.duration]))).observe({ entryTypes: ['longtask'] })
      const mes0 = w.mesActual(), c0 = mapa.getCenter(), cx = 700, cy = 425
      const ev = (tipo: string, x: number, y: number, objetivo: EventTarget) => objetivo.dispatchEvent(new MouseEvent(tipo, { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: tipo === 'mouseup' ? 0 : 1, view: window }))
      ev('mousedown', cx, cy, cv)
      const t0 = performance.now(); let ult = t0, fase = 0
      const lentos: [number, number][] = [], traza: number[] = [mes0]
      await new Promise<void>((fin) => {
        const f = (t: number) => {
          const d = t - ult; dts.push(d); if (d > 30) lentos.push([t, d]); ult = t
          if (Math.floor((t - t0) / 1000) > traza.length) traza.push(w.mesActual())
          fase += 0.07; ev('mousemove', cx + 110 * Math.sin(fase), cy + 70 * Math.sin(fase * 0.7), document)
          t - t0 < 10000 ? requestAnimationFrame(f) : fin()
        }
        requestAnimationFrame(f)
      })
      dts.shift()
      const enGesto = mapa.isMoving()
      const finGesto = new Promise<number>((res) => mapa.once('moveend', () => res(performance.now())))
      ev('mouseup', cx, cy, document)
      const tFin = await finGesto
      const mover = Math.abs(mapa.getCenter().lng - c0.lng) + Math.abs(mapa.getCenter().lat - c0.lat)
      // mes completo desde moveend (el mes sigue cambiando con la reproducción)
      let desdeFin = -1
      await new Promise<void>((fin) => {
        const f = () => {
          if (w.completo(w.mesActual())) { desdeFin = performance.now() - tFin; fin() }
          else if (performance.now() - tFin > 5000) { desdeFin = 9999; fin() }
          else requestAnimationFrame(f)
        }
        requestAnimationFrame(f)
      })
      const causa = lentos.map(([t, d]) => ({ d: +d.toFixed(0), teselas100ms: teselas.filter((x) => x > t - 100 && x <= t).length, longtask: largas.some(([s, du]) => s < t && s + du > t - d) }))
      return { dts, nLargas: largas.length, largaMax: largas.length ? Math.max(...largas.map((x) => x[1])) : 0, causa, nTeselas: teselas.length, inter: inter.n, enGesto, mover: +mover.toFixed(3), desdeFin, mesesGesto: w.mesActual() - mes0, traza, boton: document.querySelector('button[aria-label="Pausar"]') ? 'reproduciendo' : 'detenido', foco: [document.hasFocus(), document.visibilityState].join('/') }
    })
    const m1 = await fm()
    await page.screenshot({ path: `capturas/app-${ETIQ}-${vista.n}.png` })
    const { distintos, sinEstado } = await page.evaluate(() => (window as any).distintos())

    // Fase 2: mapa quieto, reproducción a 4 meses/s: fps y tiempo desde cada cambio de mes
    await page.waitForTimeout(800)
    // 2a: frames sin comprobaciones (comprobar cada frame cuesta ~10 ms y falsearía los fps)
    const fr = await page.evaluate(async () => {
      const dts: number[] = []
      let ult = performance.now(); const t0 = ult
      await new Promise<void>((fin) => { const f = (t: number) => { dts.push(t - ult); ult = t; t - t0 < 10000 ? requestAnimationFrame(f) : fin() }; requestAnimationFrame(f) })
      dts.shift()
      return dts
    })
    // 2b: tiempo desde cada cambio de mes hasta que todo lo cargado lo lleva (con comprobaciones)
    const q0 = await page.evaluate(async () => {
      const w = window as any
      const tardes: number[] = [], mesIni = w.mesActual()
      let ult = performance.now(), mes = w.mesActual(), tMes = ult, pend = true
      const t0 = ult
      await new Promise<void>((fin) => {
        const f = (t: number) => {
          const m = w.mesActual()
          if (m !== mes) { if (pend) tardes.push(9999); mes = m; tMes = t; pend = true }
          if (pend && t - tMes > 16 && w.completo(m)) { tardes.push(performance.now() - tMes); pend = false }
          t - t0 < 8000 ? requestAnimationFrame(f) : fin()
        }
        requestAnimationFrame(f)
      })
      return { tardes, mesIni, mesFin: w.mesActual() }
    })
    const q = { dts: fr, tardes: q0.tardes, mesIni: q0.mesIni, mesFin: q0.mesFin }
    const okQ = q.tardes.filter((x: number) => x < 9999)
    const frames = r.dts.length, fq = q.dts.length
    const fila = {
      vista: vista.n, zoom: vista.z, frames, fps: +(frames / (r.dts.reduce((a, b) => a + b, 0) / 1000)).toFixed(1),
      p95: +pct(r.dts, 0.95).toFixed(1), max: +Math.max(...r.dts).toFixed(1),
      cpuPorFrame: +(((m1.TaskDuration - m0.TaskDuration) * 1000) / frames).toFixed(2),
      scriptPorFrame: +(((m1.ScriptDuration - m0.ScriptDuration) * 1000) / frames).toFixed(2),
      longtasks: r.nLargas, longtaskMax: +r.largaMax.toFixed(0), teselasEvt: r.nTeselas, causa: r.causa,
      mesDesdeMoveend: +r.desdeFin.toFixed(0), mesesGesto: r.mesesGesto, traza: r.traza, boton: r.boton, centroMovido: r.mover, enGestoAlFinal: r.enGesto,
      quietoFps: +(fq / (q.dts.reduce((a, b) => a + b, 0) / 1000)).toFixed(1), quietoP95: +pct(q.dts, 0.95).toFixed(1), quietoMax: +Math.max(...q.dts).toFixed(1),
      quietoMesMed: okQ.length ? +pct(okQ, 0.5).toFixed(0) : null, quietoMesMax: okQ.length ? +Math.max(...okQ).toFixed(0) : null,
      quietoSinTerminar: q.tardes.length - okQ.length, quietoMesesAvanzados: q.mesFin - q.mesIni, quietoMeses: okQ.length,
      distintos, sinEstado, interaccion: r.inter, foco: r.foco,
    }
    fs.writeFileSync(SALIDA, JSON.stringify([...leer(), fila], null, 1))
    console.log(JSON.stringify({ ...fila, causa: undefined }))
    expect(fila.centroMovido, 'el arrastre sintético debe mover el mapa').toBeGreaterThan(0)
    expect(fila.distintos, 'recoloreado').toBeGreaterThan(5)
    expect(fila.sinEstado, 'unidades cargadas sin feature-state').toBe(0)
    expect(fila.fps).toBeGreaterThanOrEqual(58)
    expect(fila.p95).toBeLessThanOrEqual(20)
    expect(fila.max).toBeLessThanOrEqual(50)
    expect(fila.mesDesdeMoveend, 'mes completo desde moveend').toBeLessThanOrEqual(250)
    expect(fila.quietoFps).toBeGreaterThanOrEqual(58)
    expect(fila.quietoMesMax ?? 1e9).toBeLessThanOrEqual(250)
    expect(fila.quietoSinTerminar).toBe(0)
  })
}
