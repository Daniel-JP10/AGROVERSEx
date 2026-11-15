// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { BandaSerie } from '../graficos/BandaSerie'
import { anomalia, nombreVar, pedirSerie, tendencia, type RespSerie, type Num, type SerieVar } from '../datos/series'
import { paraMostrar } from '../comun/unidades'
import { tieneDatoReal } from '../datos/estatico'
import { CAPAS } from '../datos/capas'
import { useEstado } from '../app/estado'
import { t } from '../textos/i18n'
import { BASE_ULTIMO_INDICE } from '../textos/cifras'

const VARS = CAPAS.map((c) => c.id)
// IMERG Final (mm/hr) pasa a Late provisional (mm/day) en 2025-10 = índice 309; solo la lluvia cambia de fuente
const CAMBIOS_PRECIP = [{ mes: 309, texto: 'IMERG Final → Late' }]
const fmt = (x: number) => x.toFixed(3)

export function Series({ id }: { id: string }) {
  const [v, setV] = useState(useEstado.getState().capa)
  const [anom, setAnom] = useState(false)
  const [r, setR] = useState<RespSerie | null>(null)
  const [err, setErr] = useState(false)
  const real = tieneDatoReal(id)
  useEffect(() => { setR(null); setErr(false); if (real) pedirSerie(id, VARS).then(setR).catch(() => setErr(true)) }, [id, real])
  const s = r?.series[v]
  if (!real) return <p role="status">{t('panel.sinDatoReal')}</p>
  if (err) return <p role="status">{t('series.err')}</p>
  if (!s) return <p role="status">{t('series.cargando')}</p>
  const c = convertirSerie(v, s)
  if (!c) return <p role="alert">{t('unidad.sinConversion')}: {v}/{String(s.unidad_mes.find((x) => x !== null))}</p>
  let { valor } = c
  let p10: Num[] | undefined = c.p10, p90: Num[] | undefined = c.p90
  const unidad = c.unidad
  if (anom) { valor = anomalia(valor, 0, BASE_ULTIMO_INDICE); p10 = undefined; p90 = undefined }
  const tend = tendencia(valor)
  const ok = valor.filter((x) => x !== null).length
  return (
    <div>
      <label>{t('series.variable')} <select value={v} onChange={(e) => setV(e.target.value)}>{VARS.map((x) => <option key={x} value={x}>{nombreVar(x)}</option>)}</select></label>
      <label><input type="checkbox" checked={anom} onChange={(e) => setAnom(e.target.checked)} /> {t('series.anomalia')}</label>
      <BandaSerie valor={valor} p10={p10} p90={p90} variable={v} unidad={unidad} cambiosFuente={v === 'precip' ? CAMBIOS_PRECIP : []} />
      <p className="etiqueta">{ok} {t('series.de')} {valor.length} {t('series.mesesConDato')} {p10 ? t('series.delProducto') : t('series.noDisponible')}.</p>
      <p className="etiqueta">{t('series.tendencia')} {fmt(tend.pendiente * 12)} {unidad}{t('series.porAnio')} ({t('series.ic')} {fmt(tend.ic[0] * 12)} {t('series.a')} {fmt(tend.ic[1] * 12)})</p>
    </div>
  )
}

// Convierte toda la serie para mostrar con la unidad de cada mes; null si algún par (variable, unidad) no tiene conversión
export function convertirSerie(v: string, s: SerieVar) {
  try {
    const cv = (a: Num[]) => a.map((x, i) => (x === null ? null : paraMostrar(v, x, s.unidad_mes[i], i).valor))
    const u = s.unidad_mes.find((x) => x !== null) ?? null
    return { valor: cv(s.valor), p10: cv(s.p10), p90: cv(s.p90), unidad: paraMostrar(v, null, u, 0).unidad }
  } catch { return null }
}
