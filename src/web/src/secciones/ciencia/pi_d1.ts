// asistido por SI: Claude Code (Anthropic), lectura de PI-D1 mundial al umbral registrado, al 2 % y al 10 % (S1w)
// pi_d1_mundo.json es copia byte a byte de datos/procesados/series_mundo/pi_d1_mundo.json (sha256 c53ea1af...51b8)
import informe from './pi_d1_mundo.json'

export interface VarPiD1 {
  tipo_diferencia?: string
  total?: { fraccion_mayor_a?: Record<string, number> }
  unidades_con_mediana_de_la_dif_sobre_umbral?: { umbral?: number }
}
export type InformePiD1 = Record<string, { todos_los_meses?: VarPiD1 }>
export const PI_D1_INFORME = informe as InformePiD1
/** Sin IMERG Late: es provisional, 13 meses (PI_D1_FRASE_PITCH.md) */
export const VARIABLES_PI_D1_MUNDO = ['precipitacion_final', 'ndvi', 'humedad_radicular', 't2m'] as const
export const CAMPO_PI_D1 = 'pi_d1_mundo.json · <variable>.todos_los_meses.total.fraccion_mayor_a'

/** Clave del umbral registrado de la variable: relativo 0.05 -> "5%", absoluto 0.5 -> "0.5 K" */
export function claveRegistrada(v: VarPiD1): string | null {
  const u = v.unidades_con_mediana_de_la_dif_sobre_umbral?.umbral
  if (typeof u !== 'number') return null
  return v.tipo_diferencia === 'rel' ? `${Number((u * 100).toPrecision(6))}%` : `${u} K`
}

/** Umbrales registrados distintos, leídos del informe (por ejemplo "5%, 0.5 K") */
export const umbralesRegistrados = (inf: InformePiD1 | null | undefined): string =>
  [...new Set(VARIABLES_PI_D1_MUNDO.map((k) => (inf?.[k]?.todos_los_meses ? claveRegistrada(inf[k].todos_los_meses!) : null)).filter((x): x is string => !!x))].join(', ')

export type UmbralPiD1 = 'registrado' | '2%' | '10%'
/** Mínimo y máximo entre variables de la fracción de pares unidad-mes que cambian más que el umbral (0 a 1) */
export function rangoPiD1(inf: InformePiD1 | null | undefined, umbral: UmbralPiD1): { min: number; max: number; n: number } | null {
  if (!inf) return null
  const f = VARIABLES_PI_D1_MUNDO.flatMap((k) => {
    const v = inf[k]?.todos_los_meses
    if (!v) return []
    const clave = umbral === 'registrado' ? claveRegistrada(v) : umbral
    const x = clave ? v.total?.fraccion_mayor_a?.[clave] : undefined
    return typeof x === 'number' && Number.isFinite(x) ? [x] : []
  })
  return f.length ? { min: Math.min(...f), max: Math.max(...f), n: f.length } : null
}
