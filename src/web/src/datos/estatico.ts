// asistido por SI: Claude Code, lectura de los archivos estáticos de datos reales (contratos/web_datos.md v0, T-D9)
// Sin server/ ni API: la versión pública sirve estos archivos. Una matriz por variable y nivel (unidades x meses).
import { rutaPublica } from '../comun/rutas'
import { paraMostrar } from '../comun/unidades'
import { t } from '../textos/i18n'

/** Países con dato real en esta versión (carpeta datos/<iso3>/). Fuera de ellos el globo dice "sin dato real todavía". */
export const PAISES_CON_DATO: readonly string[] = ['COL']
export const iso3DeUnidad = (id: string) => id.split('-')[0]
export const tieneDatoReal = (id: string) => PAISES_CON_DATO.includes(iso3DeUnidad(id))
/** Nivel de una unidad_id: COL-ADM0, COL-ADM1-x, COL-ADM2-x */
export const nivelDeUnidad = (id: string): 0 | 1 | 2 => { const m = /-ADM([012])/.exec(id); return m ? (Number(m[1]) as 0 | 1 | 2) : 0 }

/** Estado del producto para pantalla: final o provisional (IMERG Late) */
export const textoEstado = (e: 'final' | 'provisional') => t(e === 'final' ? 'estado.final' : 'bandera.provisional')

export interface ProductoMes { producto: string; version: string; unidad: string; estado: 'final' | 'provisional' }
export interface Matriz {
  variable: string; nivel: number; mes0: string; n_meses: number
  ids: string[]; productos: ProductoMes[]; producto_mes: number[]
  valor: (number | null)[][]; p10: (number | null)[][]; p90: (number | null)[][]; frac: (number | null)[][]
}

export async function leerGz<T>(ruta: string, f: typeof fetch = fetch): Promise<T> {
  const r = await f(ruta)
  if (!r.ok) throw new Error(`${ruta}: HTTP ${r.status}`)
  return new Response(r.body!.pipeThrough(new DecompressionStream('gzip'))).json() as Promise<T>
}

const memoria = new Map<string, Promise<unknown>>()
function unaVez<T>(clave: string, leer: () => Promise<T>): Promise<T> {
  let p = memoria.get(clave) as Promise<T> | undefined
  if (!p) { p = leer(); memoria.set(clave, p); p.catch(() => memoria.delete(clave)) } // un fallo no se queda en memoria
  return p
}

export const cargarMatriz = (variable: string, nivel: number, pais = PAISES_CON_DATO[0]) =>
  unaVez(`${pais}/${variable}_${nivel}`, () => leerGz<Matriz>(rutaPublica(`datos/${pais}/${variable}_${nivel}.json.gz`)))

/** id -> [oeste, sur, este, norte, padre_id, (lon, lat si cruza el antimeridiano)] */
export type GeoUnidad = [number, number, number, number, string | null, number?, number?]
export const cargarGeo = () => unaVez('geo', () => leerGz<Record<string, GeoUnidad>>(rutaPublica('datos/unidades_geo.json.gz')))

export interface CoropletaReal {
  ids: string[]
  /** en la unidad de pantalla (paraMostrar); NaN = sin valor */
  valores: Float32Array; p10: Float32Array; p90: Float32Array; frac: Float32Array
  unidad: string
  producto: ProductoMes | null
}

const fila = (a: (number | null)[][], mes: number) => Float32Array.from(a, (r) => r[mes] ?? NaN)

/** Valores de una variable y mes para todas las unidades de un nivel, convertidos solo para mostrar. */
export async function cargarCoropleta(nivel: number, variable: string, mes: number): Promise<CoropletaReal> {
  const m = await cargarMatriz(variable, nivel)
  const pm = m.producto_mes[mes] ?? -1
  const producto = pm >= 0 ? m.productos[pm] : null
  const aMostrar = (a: (number | null)[][]) => {
    const f = fila(a, mes)
    return producto ? f.map((x) => (Number.isNaN(x) ? x : (paraMostrar(variable, x, producto.unidad, mes).valor as number))) : f
  }
  return {
    ids: m.ids, valores: aMostrar(m.valor), p10: aMostrar(m.p10), p90: aMostrar(m.p90), frac: fila(m.frac, mes),
    unidad: producto ? paraMostrar(variable, null, producto.unidad, mes).unidad : '', producto,
  }
}
