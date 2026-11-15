// asistido por SI: Claude Code, resumen con datos reales de los archivos estáticos (T-D9)
import { useEffect, useState } from 'react'
import { pedirSerie, nombreVar, type RespSerie, type SerieVar } from '../datos/series'
import { paraMostrar } from '../comun/unidades'
import { tieneDatoReal, textoEstado } from '../datos/estatico'
import { CAPAS } from '../datos/capas'
import { useEstado } from '../app/estado'
import { idioma, t } from '../textos/i18n'

const VARS = CAPAS.map((c) => c.id)
const num = (x: number) => x.toLocaleString(idioma(), { maximumFractionDigits: 2 })

export function Resumen({ id }: { id: string }) {
  const mes = useEstado((s) => s.mes)
  const [r, setR] = useState<RespSerie | null>(null)
  const [err, setErr] = useState(false)
  const real = tieneDatoReal(id)
  useEffect(() => {
    setR(null); setErr(false)
    if (real) pedirSerie(id, VARS, mes, mes).then(setR).catch(() => setErr(true))
  }, [id, mes, real])
  if (!real) return <p role="status">{t('panel.sinDatoReal')}</p>
  if (err) return <p role="alert">{t('series.err')}</p>
  if (!r) return <p role="status">{t('comun.cargando')}</p>
  return <div>{VARS.map((v) => <FilaDato key={v} v={v} s={r.series[v]} mes={mes} />)}</div>
}

// Una fila por variable con valor, rango p10 a p90 entre celdas, fracción válida, producto, versión y estado.
// Un par (variable, unidad) sin conversión se muestra como error, nunca el número crudo.
export function FilaDato({ v, s, mes }: { v: string; s: SerieVar; mes: number }) {
  const u = s.unidad_mes[0]
  let x: number | null, unidad: string, lo: number | null, hi: number | null
  try {
    const k = (n: number | null | undefined) => paraMostrar(v, n, u, mes)
    ;({ valor: x, unidad } = k(s.valor[0])); lo = k(s.p10[0]).valor; hi = k(s.p90[0]).valor
  } catch {
    return <div className="dato" role="alert"><span>{nombreVar(v)}</span><strong>{t('unidad.sinConversion')}: {v}/{String(u)}</strong></div>
  }
  const p = s.producto_mes[0] >= 0 ? s.productos[s.producto_mes[0]] : null
  const frac = s.frac[0]
  return (
    <div className="dato">
      <span>{nombreVar(v)}</span>
      <strong>{x === null ? t('comun.sinDato') : num(x)} <small>{unidad}</small></strong>
      {x !== null && lo !== null && hi !== null && <small>{t('globo.rangoCeldas')} {num(lo)}–{num(hi)} {unidad}</small>}
      <small>
        {frac !== null && `${t('globo.fraccionValida')} ${num(frac)} · `}
        {p ? `${p.producto} ${p.version} · ${textoEstado(p.estado, v, mes)}` : t('resumen.sinRegistro')}
      </small>
    </div>
  )
}
