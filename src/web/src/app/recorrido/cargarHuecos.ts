// asistido por SI: Claude Code (Anthropic), llena los huecos del guion leyendo los archivos públicos de Datos y del Gemelo
import type { Idioma } from '../../textos/i18n'

type Pedir = (url: string) => Promise<Response>

// Lotes de D-022; Web no elige parámetros ni calibraciones del gemelo, solo lee lo que trae el paquete
const LOTE_COL = 'DEMO-COL-01'
const LOTE_EEUU = 'DEMO-USA-01'
const GEMELO = 'datos/publicos/gemelo/'
const RUTA_SEGURA = /^(?!.*\.\.)[\w+\-/.]+\.json$/

const fin = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const pct = (v: number, idioma: Idioma) => new Intl.NumberFormat(idioma, { style: 'percent', maximumFractionDigits: 0 }).format(v)

/** Media, mínimo y máximo de la fracción válida mensual de HLS (meses.*.media). */
export function resumenHls(j: { meses?: Record<string, { media?: number | null }> }): { media: number; min: number; max: number } | null {
  const xs = Object.values(j.meses ?? {}).map((m) => m.media).filter(fin)
  if (!xs.length) return null
  return { media: xs.reduce((a, b) => a + b, 0) / xs.length, min: Math.min(...xs), max: Math.max(...xs) }
}

async function json<T>(pedir: Pedir, ruta: string): Promise<T> {
  const r = await pedir(import.meta.env.BASE_URL + ruta)
  if (!r.ok) throw new Error(`HTTP ${r.status} ${ruta}`)
  return r.json() as Promise<T>
}

// Cada fuente es independiente: si una falta, sus huecos quedan vacíos y el paso dice "dato no disponible"
export async function cargarHuecos(idioma: Idioma, pedir: Pedir = (u) => fetch(u)): Promise<Record<string, string>> {
  const v: Record<string, string> = {}
  const intento = async (f: () => Promise<void>) => { try { await f() } catch { /* fuente ausente */ } }
  await Promise.all([
    intento(async () => {
      const l = await json<{ lotes?: { lote_id: string; unidad_id: string; nombre?: unknown }[] }>(pedir, 'datos/lotes_demo.json')
      const eeuu = l.lotes?.find((x) => x.lote_id === LOTE_EEUU)
      const col = l.lotes?.find((x) => x.lote_id === LOTE_COL)
      const nom = (x: unknown) => (typeof x === 'string' && x ? x : undefined)
      if (nom(eeuu?.nombre)) v.nombre_lote_eeuu = eeuu!.nombre as string
      if (nom(col?.nombre)) v.nombre_lote_col = col!.nombre as string
      if (eeuu) { v.unidad_lote_eeuu = eeuu.unidad_id; v.lote_eeuu = eeuu.lote_id }
      if (col) { v.unidad_ipiales = col.unidad_id; v.lote_ipiales = col.lote_id }
    }),
    intento(async () => {
      const m = await json<{ variables?: Record<string, { meses_disponibles?: { desde?: string; hasta?: string } }> }>(pedir, 'datos/meta.json')
      const d = m.variables?.precip?.meses_disponibles
      if (d?.desde && d?.hasta) { v.mes_inicio = d.desde; v.mes_fin = d.hasta }
    }),
    ...([['ipiales', LOTE_COL], ['saunders', LOTE_EEUU]] as const).map(([nombre, lote]) => intento(async () => {
      const r = resumenHls(await json(pedir, `datos/lotes/hls_validez_${lote}.json`))
      if (!r) return
      v[`hls_validos_${nombre}`] = pct(r.media, idioma)
      v[`hls_${nombre}_min`] = pct(r.min, idioma)
      v[`hls_${nombre}_max`] = pct(r.max, idioma)
    })),
    intento(async () => {
      const ind = await json<{ lotes?: { lote_id: string; escenarios?: { historico?: { optimizacion?: string } } }[] }>(pedir, `${GEMELO}indice.json`)
      const ruta = ind.lotes?.find((x) => x.lote_id === LOTE_COL)?.escenarios?.historico?.optimizacion
      if (!ruta || !RUTA_SEGURA.test(ruta)) return
      const opt = await json<{ frente?: unknown[] }>(pedir, GEMELO + ruta)
      if (Array.isArray(opt.frente)) v.n_alternativas = String(opt.frente.length)
    }),
    // banda_antes, banda_despues e indicador_calibrado quedan sin dato hasta que el paquete del gemelo diga qué calibración mostrar
  ])
  return v
}
