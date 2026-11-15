// asistido por SI: Claude Code, pruebas de la capa de datos reales estática de Colombia (T-D9)
import { describe, expect, it, vi } from 'vitest'
import { createHash } from 'node:crypto'
import { gunzipSync, gzipSync } from 'node:zlib'
import { readFileSync } from 'node:fs'

vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {}, removeItem: () => {} })
const { cargarCoropleta, cargarMatriz, tieneDatoReal, nivelDeUnidad, PAISES_CON_DATO } = await import('../src/datos/estatico')
const { paraMostrar } = await import('../src/comun/unidades')
const { textoValor, SIN_DATO_REAL, estadoUnidad } = await import('../src/globo/coropleta')
const { capaPorId } = await import('../src/datos/capas')
const { SIN_ADM2 } = await import('../src/globo/config')
const { rutaPublica } = await import('../src/comun/rutas')

const publico = (p: string) => new URL(`../public/${p}`, import.meta.url)
const leerGz = (p: string) => JSON.parse(gunzipSync(readFileSync(publico(p))).toString('utf-8'))
// fetch de prueba: sirve public/ desde disco, igual que lo haría el alojamiento estático
vi.stubGlobal('fetch', async (ruta: string) => {
  const rel = ruta.replace(/^\//, '')
  try { return new Response(readFileSync(publico(rel))) } catch { return new Response('', { status: 404 }) }
})
const mes = (aaaamm: string) => (Number(aaaamm.slice(0, 4)) - 2000) * 12 + Number(aaaamm.slice(5)) - 1

describe('archivos estáticos de Colombia', () => {
  it('meta.json declara el mismo país que PAISES_CON_DATO', () => {
    expect([JSON.parse(readFileSync(publico('datos/meta.json'), 'utf-8')).pais]).toEqual([...PAISES_CON_DATO])
  })
  it.each(['precip', 't2m', 'sm_raiz', 'ndvi'])('%s tiene las 3 matrices con 1, 33 y 1.122 unidades de Colombia', async (v) => {
    const n = [0, 1, 2].map((k) => leerGz(`datos/COL/${v}_${k}.json.gz`))
    expect(n.map((m) => m.ids.length)).toEqual([1, 33, 1122])
    for (const m of n) {
      expect(m.ids.every((id: string) => id.startsWith('COL-') && nivelDeUnidad(id) === m.nivel)).toBe(true)
      expect(m.valor.every((f: unknown[]) => f.length === m.n_meses)).toBe(true)
    }
  })
  it('las unidades de pantalla de cada mes salen de los productos: la lluvia cambia de mm/hr a mm/day en 2025-10', async () => {
    const m = await cargarMatriz('precip', 0)
    expect(m.productos[m.producto_mes[mes('2025-09')]]).toMatchObject({ unidad: 'mm/hr', estado: 'final' })
    expect(m.productos[m.producto_mes[mes('2025-10')]]).toMatchObject({ unidad: 'mm/day', estado: 'provisional' })
  })
  it('manifiesto.json tiene hashes exactos, variables, meses disponibles y lotes_demo.json copiado de datos/lotes (D-027)', () => {
    const man = JSON.parse(readFileSync(publico('datos/manifiesto.json'), 'utf-8'))
    expect(man.version_contrato).toBe('web_datos v0')
    expect(Object.keys(man.variables).sort()).toEqual(['ndvi', 'precip', 'sm_raiz', 't2m'])
    expect(man.variables.precip.meses_disponibles).toMatchObject({ desde: '2000-01', hasta: '2026-10', n_meses_con_producto: 322 })
    expect(man.variables.ndvi.meses_disponibles).toMatchObject({ desde: '2000-02', hasta: '2026-10', n_meses_con_producto: 321 })
    expect(man.variables.ndvi.productos[0].unidad).toBe('1')
    expect(man.archivos).toHaveProperty('lotes_demo.json')
    expect(man.archivos).toHaveProperty('unidades_geo.json.gz')
    for (const [rel, info] of Object.entries(man.archivos as Record<string, { bytes: number; sha256: string }>)) {
      const b = readFileSync(publico(`datos/${rel}`))
      expect(b.byteLength, rel).toBe(info.bytes)
      expect(createHash('sha256').update(b).digest('hex'), rel).toBe(info.sha256)
    }
    const lotesPub = JSON.parse(readFileSync(publico('datos/lotes_demo.json'), 'utf-8'))
    const lotesOrig = JSON.parse(readFileSync(new URL('../../../datos/lotes/lotes_demo.json', import.meta.url), 'utf-8'))
    expect(lotesPub).toEqual(lotesOrig)
    expect(lotesPub.lotes.map((l: { lote_id: string }) => l.lote_id)).toEqual(['DEMO-USA-01', 'DEMO-COL-01'])
  })
})

describe('el mapa de Colombia con datos reales', () => {
  it('el mes inicial pinta valores distintos entre municipios (no un solo color)', async () => {
    for (const v of ['precip', 't2m', 'sm_raiz', 'ndvi']) {
      const d = await cargarCoropleta(2, v, mes('2024-06'))
      const distintos = new Set(Array.from(d.valores).filter((x) => !Number.isNaN(x)).map((x) => x.toFixed(3)))
      expect(distintos.size, v).toBeGreaterThan(100)
    }
  })
  it('al cambiar de mes, al menos una unidad cambia de valor', async () => {
    const a = await cargarCoropleta(1, 'precip', mes('2024-01')), b = await cargarCoropleta(1, 'precip', mes('2024-07'))
    expect(Array.from(a.valores).some((x, i) => x !== b.valores[i])).toBe(true)
  })
  it('los valores mostrados tienen sentido físico para Colombia', async () => {
    const rango: Record<string, [number, number]> = { precip: [0, 2000], t2m: [-5, 35], sm_raiz: [0, 1200], ndvi: [-0.2, 1] }
    for (const [v, [lo, hi]] of Object.entries(rango)) {
      const d = await cargarCoropleta(2, v, mes('2024-06'))
      const ok = Array.from(d.valores).filter((x) => !Number.isNaN(x))
      expect(ok.length, v).toBeGreaterThan(1000)
      expect(Math.min(...ok), v).toBeGreaterThanOrEqual(lo); expect(Math.max(...ok), v).toBeLessThanOrEqual(hi)
    }
  })
  it('el valor del panel (matriz, paraMostrar) coincide con el del arreglo del mapa para ese mes', async () => {
    const m = await cargarMatriz('t2m', 2), d = await cargarCoropleta(2, 't2m', mes('2024-06'))
    const i = 500, k = m.producto_mes[mes('2024-06')]
    expect(d.valores[i]).toBeCloseTo(paraMostrar('t2m', m.valor[i][mes('2024-06')], m.productos[k].unidad, '2024-06').valor as number, 3)
  })
  it('la serie mostrada no salta en el empalme Final a Late: octubre de 2025 frente a la climatología de octubre', async () => {
    const m = await cargarMatriz('precip', 0)
    const mostrado = (aaaamm: string) => paraMostrar('precip', m.valor[0][mes(aaaamm)], m.productos[m.producto_mes[mes(aaaamm)]].unidad, aaaamm).valor as number
    const oct = Array.from({ length: 10 }, (_, i) => mostrado(`${2015 + i}-10`))
    const razon = mostrado('2025-10') / (oct.reduce((a, b) => a + b, 0) / oct.length)
    expect(razon).toBeGreaterThan(0.5); expect(razon).toBeLessThan(2) // un factor 24 o 30 quedaría muy fuera
  })
  // El color sale de estadoUnidad con la escala de la capa (capas.ts) sobre el valor ya pasado por paraMostrar.
  // Criterio de "colores variados": al menos 5 de 10 tramos de la escala ocupados y menos del 20 % pegado a un extremo.
  const colores = (vals: Float32Array, rango: [number, number]) => {
    const v = Array.from(vals).filter((x) => !Number.isNaN(x)).map((x) => estadoUnidad(x, 1, rango, {}).v)
    return { tramos: new Set(v.map((x) => Math.min(9, Math.floor(x * 10)))).size, extremos: v.filter((x) => x <= 0 || x >= 1).length / v.length, mediana: v.sort((a, b) => a - b)[v.length >> 1] }
  }
  const variados = (c: ReturnType<typeof colores>) => c.tramos >= 5 && c.extremos < 0.2
  it.each([['2015-01', 'mm/hr', 'final'], ['2026-01', 'mm/day', 'provisional']])('lluvia %s (%s): colores variados con la escala en mm/mes y el crudo no lo lograría', async (aaaamm, unidad, estado) => {
    const d = await cargarCoropleta(2, 'precip', mes(aaaamm)), m = await cargarMatriz('precip', 2)
    expect(d.producto).toMatchObject({ unidad, estado }); expect(d.unidad).toBe('mm/mes')
    expect(variados(colores(d.valores, capaPorId('precip').rango)), aaaamm).toBe(true)
    // control: la misma escala sobre el valor sin convertir queda casi de un solo color
    const crudo = Float32Array.from(m.valor, (f) => f[mes(aaaamm)] ?? NaN)
    expect(variados(colores(crudo, capaPorId('precip').rango))).toBe(false)
  })
  // Sin salto en el empalme: cada mes de Late (2025-10 a 2026-10) frente a la mediana del mismo mes con Final 2001-2024,
  // en tramos de color. La mediana de esas razones debe quedar entre 0,5 y 2; un error de unidades da ~24 o ~0,04.
  // No se compara 2015-01 con 2026-01 directo: enero de 2026 es una anomalía húmeda (~3,8 veces su climatología).
  it('la lluvia no salta en el empalme: Late frente a la climatología de Final del mismo mes, en la escala de color', async () => {
    const r = capaPorId('precip').rango
    const med = (a: number[]) => a.slice().sort((x, y) => x - y)[a.length >> 1]
    const color = async (i: number) => colores((await cargarCoropleta(2, 'precip', i)).valores, r).mediana
    const razones: number[] = []
    for (let i = mes('2025-10'); i <= mes('2026-10'); i++) {
      const clima = med(await Promise.all(Array.from({ length: 24 }, (_, k) => color((2001 + k - 2000) * 12 + (i % 12)))))
      razones.push((await color(i)) / clima)
    }
    expect(med(razones)).toBeGreaterThan(0.5); expect(med(razones)).toBeLessThan(2)
  })
  it('la temperatura se pinta en °C dentro de su escala y en kelvin no lo lograría', async () => {
    const d = await cargarCoropleta(2, 't2m', mes('2015-01')), m = await cargarMatriz('t2m', 2), r = capaPorId('t2m').rango
    const ok = Array.from(d.valores).filter((x) => !Number.isNaN(x))
    expect(d.unidad).toBe('°C'); expect(Math.min(...ok)).toBeGreaterThanOrEqual(r[0]); expect(Math.max(...ok)).toBeLessThanOrEqual(r[1])
    expect(variados(colores(d.valores, r))).toBe(true)
    expect(variados(colores(Float32Array.from(m.valor, (f) => f[mes('2015-01')] ?? NaN), r))).toBe(false)
  })
  it('un mes sin producto da NaN y sin unidad, no un valor inventado', async () => {
    const d = await cargarCoropleta(0, 'ndvi', 0) // NDVI empieza en 2000-02
    expect(Number.isNaN(d.valores[0])).toBe(true); expect(d.unidad).toBe(''); expect(d.producto).toBeNull()
  })
  it('un valor nulo con fracción válida baja queda como hueco, con su fracción', async () => {
    const m = await cargarMatriz('ndvi', 2)
    const hay = m.valor.some((f, r) => f.some((x, c) => x === null && m.frac[r][c] !== null && m.frac[r][c]! < 0.5 && m.producto_mes[c] >= 0))
    expect(hay).toBe(true)
  })
})

describe('fuera de Colombia', () => {
  it('no hay dato real y el texto lo dice; el estado no pinta ni trama', () => {
    expect(tieneDatoReal('COL-ADM2-7082276B52108893597118')).toBe(true)
    expect(tieneDatoReal('VEN-ADM1-123')).toBe(false)
    expect(textoValor(undefined, 'mm/mes', [0, 500])).toBe('sin dato real todavía')
    expect(SIN_DATO_REAL).toMatchObject({ ok: false, hueco: false })
  })
  it('ninguna pieza de panel que muestra datos reales lleva la etiqueta SIMULADO', () => {
    for (const f of ['Resumen', 'Series', 'Fuentes', 'Suelo', 'PanelRegion']) {
      expect(readFileSync(new URL(`../src/paneles/${f}.tsx`, import.meta.url), 'utf-8'), f).not.toMatch(/SIMULAD/)
    }
  })
})

describe('contratos y rutas', () => {
  it('SIN_ADM2 sale de contratos/unidades.md (códigos de país), no de la base del prototipo', () => {
    const md = readFileSync(new URL('../../../contratos/unidades.md', import.meta.url), 'utf-8')
    const parr = /Códigos de país \(\d+\): ([A-Z, ]+)\./.exec(md)![1]
    expect([...SIN_ADM2].sort()).toEqual(parr.split(', ').sort())
  })
  it('las rutas públicas llevan el prefijo de despliegue', () => {
    expect(rutaPublica('teselas/adm0.pmtiles')).toBe(`${import.meta.env.BASE_URL.replace(/\/?$/, '/')}teselas/adm0.pmtiles`)
    expect(rutaPublica('/datos/meta.json')).not.toContain('//')
  })
  it('gzip propio: leerGz de la prueba y el lector de la app leen el mismo archivo', async () => {
    const buf = gzipSync(Buffer.from(JSON.stringify({ a: 1 })))
    const { leerGz: leer } = await import('../src/datos/estatico')
    expect(await leer<{ a: number }>('x', async () => new Response(buf))).toEqual({ a: 1 })
  })
  it('leerGz acepta el archivo ya descomprimido por el navegador (Content-Encoding: gzip en Vite o en el alojamiento)', async () => {
    const { leerGz: leer } = await import('../src/datos/estatico')
    expect(await leer<{ a: number }>('x', async () => new Response(JSON.stringify({ a: 1 })))).toEqual({ a: 1 })
  })
})
