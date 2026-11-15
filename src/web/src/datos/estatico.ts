// asistido por SI: Claude Code (Anthropic), lectura de los archivos estáticos de datos reales (contratos/web_datos.md v0, T-D9) y series del mundo con dos ponderaciones (S1w)
// Sin server/ ni API: la versión pública sirve estos archivos. Una matriz por variable y nivel (unidades x meses).
import { rutaPublica } from '../comun/rutas'
import { paraMostrar } from '../comun/unidades'
import { t } from '../textos/i18n'
import { etiquetaMes } from '../tiempo/valor'
import metaBuild from '../../public/datos/meta.json'
import { create } from 'zustand'

/** meta.json del despliegue (lo escribe src/mapa_estatico/construir.py); sin series del mundo queda el de public/ (solo COL) */
export interface Meta {
  pais?: string; paises?: string[]; paises_adm2?: string[]; mundo?: string
  ponderaciones?: Record<string, string>; ponderacion_defecto?: string; variables?: unknown
}
/** Países con dato real: salen de meta.json (paises), nunca de una constante. Se rellena al leer el meta del despliegue. */
export const PAISES_CON_DATO: string[] = [...((metaBuild as Meta).paises ?? [(metaBuild as Meta).pais ?? 'COL'])]
let META: Meta = metaBuild as Meta
export const metaActual = () => META
/** Lee datos/meta.json del despliegue una vez y actualiza PAISES_CON_DATO. */
export const cargarMeta = () => unaVez('meta', async () => {
  const r = await fetch(rutaPublica('datos/meta.json'))
  if (!r.ok) throw new Error(`meta.json: HTTP ${r.status}`)
  META = (await r.json()) as Meta
  PAISES_CON_DATO.splice(0, PAISES_CON_DATO.length, ...(META.paises ?? [META.pais ?? 'COL']))
  return META
})
export const hayMundo = () => !!META.mundo

export type Ponderacion = 'cultivo' | 'area'
/** Cultivo por defecto; el área se elige en el modo Technical (traspaso S1w) */
export const usePonderacion = create<{ ponderacion: Ponderacion; set: (p: Ponderacion) => void }>((set) => ({ ponderacion: 'cultivo', set: (ponderacion) => set({ ponderacion }) }))
/** Ponderación que de verdad se lee: sin series del mundo solo existe la de área (COL de public/) */
export const ponderacionEfectiva = (): Ponderacion => (hayMundo() ? usePonderacion.getState().ponderacion : 'area')
/** Ruta del archivo: adm0 y adm1 en MUNDO/, adm2 por país; cultivo con su sufijo (contratos/web_datos.md §7) */
export function rutaMatriz(variable: string, nivel: number, pais: string, pond: Ponderacion, meta: Meta = META): string {
  if (!meta.mundo) return `datos/${pais}/${variable}_${nivel}.json.gz`
  const suf = meta.ponderaciones?.[pond] ?? ''
  return nivel < 2 ? `datos/${meta.mundo}/${variable}_${nivel}${suf}.json.gz` : `datos/${pais}/${variable}_${nivel}${suf}.json.gz`
}
export const iso3DeUnidad = (id: string) => id.split('-')[0]
export const tieneDatoReal = (id: string) => PAISES_CON_DATO.includes(iso3DeUnidad(id))
/** Nivel de una unidad_id: COL-ADM0, COL-ADM1-x, COL-ADM2-x */
export const nivelDeUnidad = (id: string): 0 | 1 | 2 => { const m = /-ADM([012])/.exec(id); return m ? (Number(m[1]) as 0 | 1 | 2) : 0 }

/** Estado del producto para pantalla: final o provisional (IMERG Late) */
// Meses con un valor raro de causa PENDIENTE (hallazgo de ene y feb de 2026, ~3-4 veces la climatología; director 19:5x).
// Salen como provisionales en revisión hasta confirmar la causa con fuentes independientes.
export const MESES_EN_REVISION: Readonly<Record<string, readonly string[]>> = { precip: ['2026-01', '2026-02'] }
export const enRevision = (variable: string, mes: number) => !!MESES_EN_REVISION[variable]?.includes(etiquetaMes(mes))
export const textoEstado = (e: 'final' | 'provisional', variable?: string, mes?: number) =>
  variable !== undefined && mes !== undefined && enRevision(variable, mes) ? `${t('bandera.provisional')} · ${t('estado.enRevision')}` : t(e === 'final' ? 'estado.final' : 'bandera.provisional')

export interface ProductoMes { producto: string; version: string; unidad: string; estado: 'final' | 'provisional' }
export interface Matriz {
  variable: string; nivel: number; mes0: string; n_meses: number
  ids: string[]; productos: ProductoMes[]; producto_mes: number[]
  valor: (number | null)[][]; p10: (number | null)[][]; p90: (number | null)[][]; frac: (number | null)[][]
  /** ids sin cultivo en todos sus meses (solo en la ponderación de cultivo): "No cropland", nunca 0 */
  sin_cultivo?: string[]; ponderacion?: string
}

export async function leerGz<T>(ruta: string, f: typeof fetch = fetch): Promise<T> {
  const r = await f(ruta)
  if (!r.ok) throw new Error(`${ruta}: HTTP ${r.status}`)
  // Si el servidor manda Content-Encoding: gzip (Vite en desarrollo, algunos alojamientos), el navegador ya lo descomprimió
  const b = new Uint8Array(await r.arrayBuffer())
  if (b[0] !== 0x1f || b[1] !== 0x8b) return JSON.parse(new TextDecoder().decode(b)) as T
  return new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('gzip'))).json() as Promise<T>
}

const memoria = new Map<string, Promise<unknown>>()
function unaVez<T>(clave: string, leer: () => Promise<T>): Promise<T> {
  let p = memoria.get(clave) as Promise<T> | undefined
  if (!p) { p = leer(); memoria.set(clave, p); p.catch(() => memoria.delete(clave)) } // un fallo no se queda en memoria
  return p
}

export async function cargarMatriz(variable: string, nivel: number, pais = PAISES_CON_DATO[0], pond: Ponderacion = ponderacionEfectiva()): Promise<Matriz> {
  await cargarMeta().catch(() => undefined) // sin meta del despliegue se queda el de public/
  const ruta = rutaMatriz(variable, nivel, pais, hayMundo() ? pond : 'area')
  return unaVez(ruta, () => leerGz<Matriz>(rutaPublica(ruta)))
}

/** id -> [oeste, sur, este, norte, padre_id, (lon, lat si cruza el antimeridiano)] */
export type GeoUnidad = [number, number, number, number, string | null, number?, number?]
export const cargarGeo = () => unaVez('geo', () => leerGz<Record<string, GeoUnidad>>(rutaPublica('datos/unidades_geo.json.gz')))

export interface CoropletaReal {
  ids: string[]
  /** en la unidad de pantalla (paraMostrar); NaN = sin valor */
  valores: Float32Array; p10: Float32Array; p90: Float32Array; frac: Float32Array
  unidad: string
  producto: ProductoMes | null
  sinCultivo: Set<string>
}

const fila = (a: (number | null)[][], mes: number) => Float32Array.from(a, (r) => r[mes] ?? NaN)

// Une matrices de varios países (adm2): mismas columnas, filas seguidas
function unir(ms: Matriz[]): Matriz {
  if (ms.length === 1) return ms[0]
  const b = ms[0]
  return {
    ...b, ids: ms.flatMap((m) => m.ids), valor: ms.flatMap((m) => m.valor), p10: ms.flatMap((m) => m.p10), p90: ms.flatMap((m) => m.p90),
    frac: ms.flatMap((m) => m.frac), sin_cultivo: ms.flatMap((m) => m.sin_cultivo ?? []),
  }
}

/** Valores de una variable y mes para todas las unidades de un nivel, convertidos solo para mostrar. En adm2 del mundo, solo de `paises`. */
export async function cargarCoropleta(nivel: number, variable: string, mes: number, paises?: string[]): Promise<CoropletaReal> {
  await cargarMeta().catch(() => undefined)
  const lista = nivel === 2 && hayMundo() ? (paises ?? []).filter((p) => META.paises_adm2?.includes(p)) : [PAISES_CON_DATO[0]]
  const vacia: Matriz = { variable, nivel, mes0: '', n_meses: 0, ids: [], productos: [], producto_mes: [], valor: [], p10: [], p90: [], frac: [] }
  const m = lista.length ? unir(await Promise.all(lista.map((p) => cargarMatriz(variable, nivel, p)))) : vacia
  const pm = m.producto_mes[mes] ?? -1
  const producto = pm >= 0 ? m.productos[pm] : null
  const aMostrar = (a: (number | null)[][]) => {
    const f = fila(a, mes)
    return producto ? f.map((x) => (Number.isNaN(x) ? x : (paraMostrar(variable, x, producto.unidad, mes).valor as number))) : f
  }
  return {
    ids: m.ids, valores: aMostrar(m.valor), p10: aMostrar(m.p10), p90: aMostrar(m.p90), frac: fila(m.frac, mes),
    unidad: producto ? paraMostrar(variable, null, producto.unidad, mes).unidad : '', producto,
    sinCultivo: new Set(m.sin_cultivo ?? []),
  }
}
