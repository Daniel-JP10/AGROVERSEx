// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// PoC descartable: recoloreo de ADM2 (~50 mil unidades) sobre el globo. Variante por ?v=A|B|C|D.
import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'

maplibregl.setWorkerUrl(workerUrl)
maplibregl.addProtocol('pmtiles', new Protocol().tile)

export type Variante = 'A' | 'B' | 'C' | 'D'
const P = new URLSearchParams(location.search)
const DATOS = `http://localhost:${P.get('pd') || 5198}`
const RANURA = Number(P.get('n') || 2000) // tamaño de rebanada de B
const VALIDAR = P.get('val') === '1' // C: validar la expresión (lento) o no
const FUENTE = 'adm2', CAPA = 'adm2'

// Paleta del pre-esqueleto, interpolada en JS para C
const PAL: [number, [number, number, number]][] = [[0, [138, 74, 40]], [0.35, [201, 154, 74]], [0.6, [155, 178, 106]], [1, [43, 143, 147]]]
export function color(v: number): string {
  v = Math.min(1, Math.max(0, v))
  let i = 1
  while (i < PAL.length - 1 && v > PAL[i][0]) i++
  const [t0, c0] = PAL[i - 1], [t1, c1] = PAL[i], k = (v - t0) / (t1 - t0)
  return `rgb(${c0.map((x, j) => Math.round(x + (c1[j] - x) * k)).join(',')})`
}

// Valores sintéticos deterministas (SIMULADO): hash entero de (unidad, mes)
export function valoresDelMes(n: number, mes: number): Float32Array {
  const out = new Float32Array(n)
  for (let i = 0; i < n; i++) {
    let h = Math.imul(i + 1, 0x9e3779b1) ^ Math.imul(mes + 1, 0x85ebca6b)
    h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d); h ^= h >>> 12
    out[i] = (h >>> 0) / 4294967296
  }
  return out
}

const mapa = new maplibregl.Map({
  container: 'mapa',
  style: {
    version: 8, projection: { type: 'globe' },
    sources: {
      adm1: { type: 'vector', url: `pmtiles://${DATOS}/adm1.pmtiles`, promoteId: 'id' },
      adm2: { type: 'vector', url: `pmtiles://${DATOS}/adm2.pmtiles`, promoteId: 'id' },
    },
    layers: [
      { id: 'fondo', type: 'background', paint: { 'background-color': '#0b1a2e' } },
      { id: 'adm1-relleno', type: 'fill', source: 'adm1', 'source-layer': 'adm1', maxzoom: 6, paint: { 'fill-color': '#4a6a5a', 'fill-opacity': 0.62 } },
      {
        id: 'adm2-relleno', type: 'fill', source: FUENTE, 'source-layer': CAPA, minzoom: 6,
        paint: { 'fill-color': ['interpolate', ['linear'], ['coalesce', ['feature-state', 'v'], 0.5], ...PAL.flatMap(([t, c]) => [t, `rgb(${c.join(',')})`])], 'fill-opacity': 0.62 },
      },
      { id: 'adm2-linea', type: 'line', source: FUENTE, 'source-layer': CAPA, minzoom: 6, paint: { 'line-color': '#0b0e12', 'line-opacity': 0.55, 'line-width': 0.5 } },
    ],
  } as maplibregl.StyleSpecification,
  center: [P.has('lng') ? Number(P.get('lng')) : -74, P.has('lat') ? Number(P.get('lat')) : 4.5],
  zoom: Number(P.get('z') || 6), maxPitch: 70, attributionControl: false,
  canvasContextAttributes: { antialias: true },
})

let cache: Set<string> | null = null // ids visibles; se invalida al llegar teselas
let aplicado = new Map<string, number>() // id -> mes ya escrito en feature-state
let generacion = 0
let reanudar: (() => void) | null = null
let idxMemo: { ids: string[]; idx: Map<string, number> } | null = null

function indiceDe(ids: string[]) {
  if (idxMemo?.ids !== ids) idxMemo = { ids, idx: new Map(ids.map((id, i) => [id, i])) }
  return idxMemo.idx
}
function visibles(): Set<string> {
  if (!cache) {
    cache = new Set()
    for (const f of mapa.querySourceFeatures(FUENTE, { sourceLayer: CAPA })) cache.add(String(f.properties.id))
  }
  return cache
}
mapa.on('sourcedata', (e) => {
  if (e.sourceId === FUENTE && (e as any).tile) { cache = null; reanudar?.() }
})

const ref = (id: string) => ({ source: FUENTE, sourceLayer: CAPA, id })
const rAF = () => new Promise<void>((r) => requestAnimationFrame(() => r()))

/**
 * Confirma que todo lo cargado (ids de querySourceFeatures) lleva el valor del mes.
 * El `state` de querySourceFeatures NO refleja el feature-state en MapLibre 6.16 (queda en
 * undefined durante segundos), así que el estado se lee con getFeatureState.
 */
function confirmado(valores: Float32Array, idx: Map<string, number>): boolean {
  for (const f of mapa.querySourceFeatures(FUENTE, { sourceLayer: CAPA })) {
    const id = String(f.properties.id), i = idx.get(id)
    if (i !== undefined && (mapa.getFeatureState(ref(id)) as any).v !== valores[i]) return false
  }
  return true
}
const siguienteRender = () => new Promise<void>((r) => { mapa.triggerRepaint(); mapa.once('render', () => r()) })

export async function aplicarMes(v: Variante, mes: number, valores: Float32Array, ids: string[]): Promise<{ ms: number }> {
  const t0 = performance.now()
  const idx = indiceDe(ids)
  const mia = ++generacion
  if (v === 'A') {
    // Línea base: todas las unidades del índice, de una vez
    for (let i = 0; i < ids.length; i++) mapa.setFeatureState(ref(ids[i]), { v: valores[i] })
    await siguienteRender()
    return { ms: confirmado(valores, idx) ? performance.now() - t0 : -2 }
  }
  if (v === 'B') {
    // Rebanadas de RANURA por frame sobre las unidades cargadas que aún no llevan este mes
    const trabajar = (): Promise<boolean> => new Promise((fin) => {
      const paso = () => {
        if (mia !== generacion) return fin(false) // superada por un mes nuevo
        let n = 0
        for (const id of visibles()) {
          if (aplicado.get(id) === mes) continue
          const i = idx.get(id)
          if (i === undefined) continue
          mapa.setFeatureState(ref(id), { v: valores[i] })
          aplicado.set(id, mes)
          if (++n >= RANURA) return void requestAnimationFrame(paso)
        }
        fin(true)
      }
      paso()
    })
    // Llegan teselas después de terminar: se sigue aplicando el mes vigente (no se suelta nunca)
    let corriendo = false
    reanudar = () => {
      if (corriendo || mia !== generacion) return
      corriendo = true
      requestAnimationFrame(() => trabajar().then(() => (corriendo = false)))
    }
    for (;;) {
      if (!(await trabajar())) return { ms: -1 }
      await siguienteRender()
      if (mia !== generacion) return { ms: -1 }
      if (confirmado(valores, idx)) return { ms: performance.now() - t0 }
    }
  }
  if (v === 'C') {
    const expr: unknown[] = ['match', ['get', 'id']]
    for (let i = 0; i < ids.length; i++) expr.push(ids[i], color(valores[i]))
    expr.push('rgb(128,128,128)')
    mapa.setPaintProperty('adm2-relleno', 'fill-color', expr as any, { validate: VALIDAR })
    await new Promise<void>((r) => mapa.once('render', () => r()))
    await rAF()
    return { ms: performance.now() - t0 }
  }
  throw new Error('D requiere `idx` entero en las teselas (no implementada)')
}

export async function cargarIds(): Promise<string[]> {
  const r = await fetch(`${DATOS}/indice.json.gz`)
  const txt = await new Response(r.body!.pipeThrough(new DecompressionStream('gzip'))).text()
  return (JSON.parse(txt) as { id: string; nivel: number }[]).filter((x) => x.nivel === 2).map((x) => x.id)
}

;(window as any).poc = { mapa, aplicarMes, cargarIds, valoresDelMes }
// Al cargar, pinta el mes 0 (si no, abrir la página a mano muestra una sola tinta); ?auto=0 lo evita
mapa.on('load', async () => {
  if (P.get('auto') !== '0' && P.get('v') !== 'D') {
    const ids = await cargarIds()
    await aplicarMes((P.get('v') || 'B') as Variante, 0, valoresDelMes(ids.length, 0), ids)
  }
  ;(window as any).pocListo = true
})
