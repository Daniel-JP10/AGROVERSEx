// asistido por SI: Claude Code (Anthropic), lectura de los paquetes del gemelo en public/gemelo y del relieve en public/lotes
import { useEffect, useState } from 'react'
import { idioma, t, useIdioma, type ClaveTodo, type Idioma } from '../../textos/i18n'
import type { EstrategiaGemelo, Rotulo, EntradaTexto, Tarjeta } from '../rotaciones/gemelo'
import type { AlertaHeladaGemelo } from '../rotaciones/AlertaHelada'
import type { Catalogo } from '../rotaciones/textosGemelo'
import { traducir } from '../rotaciones/textosGemelo'
import { corregirCatalogoEn } from '../rotaciones/correccionEn'
import { LOTE_DEMO } from '../rotaciones/lector'
import { UNIDADES_TRAYECTORIA, type VariableTrayectoria } from './unidades'

export const LOTE_POR_DEFECTO = 'DEMO-COL-01'
// Los 7 escenarios en el orden de lote.json (escenarios y luego escenarios_enso)
export type Escenario = string
const RUTA_SEGURA = /^(?!.*\.\.)[\w+\-/.]+\.json$/

export interface Temporada { cultivo: string; siembra: string; cosecha?: string }
export type EstrategiaSim = EstrategiaGemelo & { temporadas: Temporada[] }
export interface Simulacion {
  metadatos: { horizonte_anios: number; metodo_eto: string; rotulo?: Rotulo; miembros?: { parametros?: number } }
  clima: { fuente: string; anios: [number, number] }
  suelo: { fuente: string }
  escenario: { tipo: string }
  alertas?: { helada_etapa_sensible?: AlertaHeladaGemelo & { avisos?: EntradaTexto[] } }
  estrategias: EstrategiaSim[]
  prioridades: { valores: Record<string, Record<string, number | null>>; pesos_iguales: { orden: string[] } }
  avisos_claves?: EntradaTexto[]
  tarjetas?: Record<string, Tarjeta>
}
export interface LoteJson {
  lote_id: string
  nombre: string
  escenarios: Record<string, { simulacion: string; optimizacion?: string }>
  escenarios_enso: Record<string, { simulacion: string }>
  rotulo?: Rotulo
}
export interface Relieve {
  producto: string; crs_metrico: string
  elevacion_p10_p50_p90_m: [number, number, number]
  pendiente_media_m_m: number
  pendiente_p10_p50_p90_m_m: [number, number, number]
}
export interface Perfil {
  crs_destino: string; celda_m: number; exageracion_vertical: number
  distancia_m: number[]; elevacion_m: number[]; indice_centro: number
  leyenda_relieve_m: [number, number]; leyenda_pendiente_m_m: [number, number]
}

export type EstadoLote =
  | { estado: 'cargando' }
  | { estado: 'sin_dato' }
  | { estado: 'listo'; lote: LoteJson; sim: Simulacion; cat: Catalogo; relieve?: Relieve; perfil?: Perfil }

type Pedir = (url: string) => Promise<Response>
async function json<T>(pedir: Pedir, ruta: string): Promise<T> {
  const r = await pedir(import.meta.env.BASE_URL + ruta)
  if (!r.ok) throw new Error(`HTTP ${r.status} ${ruta}`)
  return r.json() as Promise<T>
}
const opcional = <T,>(p: Promise<T>) => p.catch(() => undefined)

export const escenariosDe = (l: LoteJson): string[] => [...Object.keys(l.escenarios), ...Object.keys(l.escenarios_enso)]

/** Lee lote.json, la simulación del escenario, el catálogo de textos y el relieve; si falta lo esencial, sin_dato. */
export async function cargarLote(lote: string, escenario: string, lang: Idioma, pedir: Pedir = (u) => fetch(u)): Promise<EstadoLote> {
  if (!LOTE_DEMO.test(lote)) return { estado: 'sin_dato' }
  try {
    const [l, indice] = await Promise.all([json<LoteJson>(pedir, `gemelo/${lote}/lote.json`), json<{ textos: Record<Idioma, string> }>(pedir, 'gemelo/indice.json')])
    const ruta = l.escenarios[escenario]?.simulacion ?? l.escenarios_enso[escenario]?.simulacion
    const rutaCat = indice.textos?.[lang]
    if (!ruta || !RUTA_SEGURA.test(ruta) || !rutaCat || !RUTA_SEGURA.test(rutaCat)) return { estado: 'sin_dato' }
    const [sim, cat, rel, perfil] = await Promise.all([
      json<Simulacion>(pedir, `gemelo/${ruta}`), json<Catalogo>(pedir, `gemelo/${rutaCat}`),
      opcional(json<{ lotes: Record<string, Relieve> }>(pedir, 'lotes/relieve_lotes.json')), opcional(json<Perfil>(pedir, `lotes/perfil_${lote}.json`)),
    ])
    if (!Array.isArray(sim?.estrategias) || !sim.estrategias.length) return { estado: 'sin_dato' }
    return { estado: 'listo', lote: l, sim, cat: lang === 'en' ? corregirCatalogoEn(cat) : cat, relieve: rel?.lotes?.[lote], perfil }
  } catch {
    return { estado: 'sin_dato' }
  }
}

export function useLote(lote: string, escenario: string): EstadoLote {
  const lang = useIdioma()
  const clave = `${lote}|${escenario}|${lang}`
  const [hecho, setHecho] = useState<{ clave: string; e: EstadoLote } | null>(null)
  useEffect(() => {
    let vivo = true
    void cargarLote(lote, escenario, lang).then((e) => { if (vivo) setHecho({ clave, e }) })
    return () => { vivo = false }
  }, [lote, escenario, lang, clave])
  // Al cambiar de escenario o idioma se sigue mostrando lo anterior hasta que llega lo nuevo (sin parpadeo)
  return hecho ? hecho.e : { estado: 'cargando' }
}

/** Lote de ?lote= en el hash (cualquier sección); por defecto el lote DEMO de Colombia. */
export function loteDeHash(hash: string): string {
  const v = new URLSearchParams(hash.split('?')[1] ?? '').get('lote')
  return v && LOTE_DEMO.test(v) ? v : LOTE_POR_DEFECTO
}

// Formato y textos comunes de lote y rotaciones
// Enteros (días, conteos) completos; el resto con 3 cifras significativas
export const fmt = (v: number) => new Intl.NumberFormat(idioma(), Number.isInteger(v) ? { maximumFractionDigits: 0 } : { maximumSignificantDigits: 3 }).format(v)
export const llenar = (texto: string, vars: Record<string, string | number>) =>
  texto.replace(/\{(\w+)\}/g, (todo, k) => (k in vars ? (typeof vars[k] === 'number' ? fmt(vars[k] as number) : String(vars[k])) : todo))
export const fin = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)

const CULTIVOS = ['papa', 'avena', 'frijol', 'maiz', 'soya']
const cultivo = (c: string) => (CULTIVOS.includes(c) ? t(`lote.cultivo_${c}` as ClaveTodo) : c)
/** En inglés, la secuencia traducida; en español, el nombre del paquete. */
export const nombreEstrategia = (e: Pick<EstrategiaGemelo, 'nombre' | 'secuencia'>) =>
  idioma() === 'es' ? e.nombre : e.secuencia.split(/\s*->\s*/).map(cultivo).join(' → ')
export const nombreCultivo = cultivo

/** Unidad visible de una variable de la trayectoria; sale de UNIDADES_TRAYECTORIA (atada al contrato). */
export function unidadVariable(v: VariableTrayectoria): string {
  const u = UNIDADES_TRAYECTORIA[v]
  if (v === 'agua_raiz') return t('lote.u_agua_raiz')
  if (v === 'P' || v === 'ETa') return t('lote.u_mm_mes')
  return u === 'mm' ? t('lote.u_mm') : u === 'kg N/ha' ? t('lote.u_kgn') : t('lote.u_fraccion')
}
/** Unidad de un indicador traducida con el catálogo del gemelo (unit.<unidad>). */
// El catálogo inglés deja 'índice' sin traducir; se usa la clave propia
export const unidadIndicador = (cat: Catalogo, u: string) => (u === 'índice' ? t('lote.u_indice') : cat[`unit.${u}`] ? traducir(cat, `unit.${u}`) : u)
export const nombreEscenario = (cat: Catalogo, e: string) => (cat[`scenario.${e}`] ? traducir(cat, `scenario.${e}`) : e)
