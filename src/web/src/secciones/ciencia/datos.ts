// asistido por SI: Claude Code (Anthropic), cifras de Ciencia y validación leídas en el build de los archivos de datos (plan v2 §6)
// Ninguna cifra se escribe a mano: todo sale de estos JSON. Solo se importan los campos agregados que se muestran
// (las importaciones con nombre dejan fuera del bundle el resto del archivo, por ejemplo las estaciones de S4).
import comparacionPowerImerg from '../../../../../datos/lotes/comparacion_power_imerg.json'
import { comparaciones as compTemperatura, periodo as periodoTemperatura } from '../../../../../datos/lotes/validacion_temperatura_ipiales.json'
import hlsCol from '../../../../../datos/lotes/hls_validez_DEMO-COL-01.json'
import hlsUsa from '../../../../../datos/lotes/hls_validez_DEMO-USA-01.json'
import { imerg_colombia_adm0_late_frente_a_final as s4Imerg, power as s4Power } from '../../../../../datos/evidencia/S4_hallazgo_lluvia_2026.json'
import piD1Colombia from '../../../../../datos/evidencia/T-D2_pi_d1_colombia_2019_4var.json'
import { lotes as erosionLotes } from '../../../../../datos/lotes/exposicion_erosiva_lotes.json'

// Archivo y campo de cada tarjeta: se muestran como fuente
export const ARCHIVOS = {
  estacion: 'datos/lotes/comparacion_power_imerg.json · contraste_estacion_ghcn_com00080370',
  temperatura: 'datos/lotes/validacion_temperatura_ipiales.json · comparaciones.T2M_MIN_vs_TMIN',
  hls: 'datos/lotes/hls_validez_<lote>.json · meses',
  s4: 'datos/evidencia/S4_hallazgo_lluvia_2026.json · imerg_colombia_adm0_late_frente_a_final, power.anomalia_colombia',
  piD1: 'datos/evidencia/T-D2_pi_d1_colombia_2019_4var.json · fraccion_unidades_con_dif_relativa_mayor_a',
  piD1Mundo: 'datos/procesados/series_mundo/pi_d1_mundo.json · total.fraccion_mayor_a',
  erosion: 'datos/lotes/exposicion_erosiva_lotes.json · exposicion_potencial_suelo_desnudo_100pct, sensibilidad_imerg',
} as const

// 1. Lluvia de POWER e IMERG frente al pluviómetro de San Luis (Ipiales), lote COL
const ghcn = comparacionPowerImerg.find((l) => l.lote_id === 'DEMO-COL-01')?.contraste_estacion_ghcn_com00080370
export const estacion = ghcn ? {
  periodo: comparacionPowerImerg.find((l) => l.lote_id === 'DEMO-COL-01')!.periodo,
  power: ghcn.sesgo_relativo_power_vs_ghcn,
  imerg: ghcn.sesgo_relativo_imerg_vs_ghcn,
  dias: ghcn.n_dias_comunes_con_pluviometro,
  fraccion: ghcn.fraccion_dias_usados,
} : null

// 2. Tmín corregida a la altura del lote frente a GHCN; la cruda es la línea base. El nivel del intervalo sale del nombre del campo
const tmin = compTemperatura.T2M_MIN_vs_TMIN
const nivelIc = (campo: string) => Number(/_ic(\d+)_/.exec(campo)?.[1])
export const temperatura = {
  periodo: periodoTemperatura,
  nivel: nivelIc('sesgo_c_ic95_bootstrap_anual'),
  corregida: { sesgo: tmin.corregida_lote_2934m.sesgo_c, sesgoIc: tmin.corregida_lote_2934m.sesgo_c_ic95_bootstrap_anual, mae: tmin.corregida_lote_2934m.mae_c, maeIc: tmin.corregida_lote_2934m.mae_c_ic95_bootstrap_anual, n: tmin.corregida_lote_2934m.n_dias_validos, fraccion: tmin.corregida_lote_2934m.fraccion_valida },
  cruda: { sesgo: tmin.cruda_2553m.sesgo_c, sesgoIc: tmin.cruda_2553m.sesgo_c_ic95_bootstrap_anual },
}

// 3. Fracción de vistas HLS válidas por mes y lote; la banda va del q05 al q95 de los píxeles
type MesHls = { n_escenas: number; media: number; q05: number; q95: number }
const resumenHls = (d: { lote_id: string; periodo: string[]; meses: Record<string, MesHls> }) => {
  const meses = Object.entries(d.meses).sort(([a], [b]) => a.localeCompare(b)).map(([mes, m]) => ({ mes, ...m }))
  const medias = meses.map((m) => m.media).sort((a, b) => a - b)
  const mitad = Math.floor(medias.length / 2)
  return {
    lote: d.lote_id, periodo: d.periodo, meses,
    mediana: medias.length % 2 ? medias[mitad] : (medias[mitad - 1] + medias[mitad]) / 2,
    min: medias[0], max: medias[medias.length - 1],
  }
}
export const hls = [resumenHls(hlsCol), resumenHls(hlsUsa)]
// Percentiles de la banda, leídos de los nombres de campo q05 y q95 (D-039 punto 3: la cifra sale del campo que se usa)
export const CAMPOS_BANDA_HLS = ['q05', 'q95'] as const
export const bandaHls = { bajo: Number(CAMPOS_BANDA_HLS[0].slice(1)), alto: Number(CAMPOS_BANDA_HLS[1].slice(1)) }

// 4. Lluvia de enero y febrero de 2026 frente a la climatología (IMERG Late, meses provisionales) y POWER
export const lluvia2026 = (['2026-01', '2026-02'] as const).map((mes) => ({
  mes,
  imerg: s4Imerg[mes],
  power: s4Power.anomalia_colombia[mes],
}))

// 5. PI-D1 Colombia 2019: fracción de unidades-mes cuyo valor cambia más que un umbral al ponderar solo cultivo
export const VARIABLES_PI_D1 = ['precipitacion_final', 'ndvi', 't2m', 'humedad_radicular'] as const
// Los dos umbrales que cita el plan (v2 §7.2) son claves del archivo; el número que se muestra sale de la clave
export const UMBRALES_PI_D1 = ['10%', '2%'] as const
export const piD1 = VARIABLES_PI_D1.map((v) => {
  const d = piD1Colombia[v]
  const [alto, bajo] = UMBRALES_PI_D1.map((u) => ({ umbral: parseFloat(u), fraccion: d.fraccion_unidades_con_dif_relativa_mayor_a[u] }))
  return { variable: v, n: d.unidades_mes_con_cultivo_y_valor, meses: d.meses, alto, bajo }
})

// 6. PI-D1 mundial (S1): oculto hasta que el orquestador lo integre con su verificador (plan v2 §7)
export type InformePiD1Mundo = Record<string, { total?: { fraccion_mayor_a?: Record<string, number> } }>
export const PI_D1_MUNDO: InformePiD1Mundo | null = null
/** Rango entre variables de la fracción de unidades-mes que cambia, para el umbral más alto y el más bajo del informe. */
export function rangoPiD1Mundo(informe: InformePiD1Mundo | null): { min: number; max: number; umbralAlto: number; umbralBajo: number } | null {
  if (!informe) return null
  const filas = Object.values(informe).flatMap((v) => Object.entries(v.total?.fraccion_mayor_a ?? {}).map(([u, f]) => ({ u: parseFloat(u), f })))
    .filter((x) => Number.isFinite(x.u) && Number.isFinite(x.f))
  if (!filas.length) return null
  const umbralAlto = Math.max(...filas.map((x) => x.u)), umbralBajo = Math.min(...filas.map((x) => x.u))
  const alto = filas.filter((x) => x.u === umbralAlto).map((x) => x.f), bajo = filas.filter((x) => x.u === umbralBajo).map((x) => x.f)
  return { min: Math.min(...alto), max: Math.max(...bajo), umbralAlto, umbralBajo }
}

// 7. Exposición erosiva de suelo desnudo: POWER es la base y IMERG la sensibilidad a la fuente de lluvia
export const erosion = Object.values(erosionLotes).map((l) => ({
  lote: l.lote_id,
  periodo: l.periodo,
  base: l.exposicion_potencial_suelo_desnudo_100pct.indice_exposicion_erosiva,
  imerg: l.sensibilidad_imerg.exposicion_potencial_suelo_desnudo_100pct.indice_exposicion_erosiva,
  pendiente: l.relieve_nasadem_30m.pendiente_p10_p50_p90_m_m,
}))
