// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { clienteDefecto } from '../datos/consultas'
import { pedirSerie, nombreVar, type RespSerie, type SerieVar } from '../datos/series'
import { paraMostrar } from '../comun/unidades'
import { rotulosDeVariable } from '../datos/banderas'
import { useEstado } from '../app/estado'
import type { DetalleUnidad } from '../datos/tipos'
import { Chip } from './Chip'
import { t } from '../textos/i18n'

const VARS = ['precip', 't2m', 'ndvi']
// Clases 1 a 30 de Beck et al. 2023 (legend.txt)
const KOPPEN = 'Af Am Aw BWh BWk BSh BSk Csa Csb Csc Cwa Cwb Cwc Cfa Cfb Cfc Dsa Dsb Dsc Dsd Dwa Dwb Dwc Dwd Dfa Dfb Dfc Dfd ET EF'.split(' ')
const condicion = () => [t('resumen.degradada'), t('resumen.estable'), t('resumen.mejora')]
const num = (x: number) => x.toLocaleString('es', { maximumFractionDigits: 2 })

export function Resumen({ id }: { id: string }) {
  const mes = useEstado((s) => s.mes)
  const [d, setD] = useState<DetalleUnidad | null>(null)
  const [r, setR] = useState<RespSerie | null>(null)
  const [anual, setAnual] = useState<{ anio: number; clase_condicion: number | null }[]>([])
  useEffect(() => { setD(null); clienteDefecto.unidad(id).then(setD).catch(() => {}) }, [id])
  useEffect(() => { setAnual([]); fetch(`/api/anual/${encodeURIComponent(id)}`).then((x) => x.json()).then((x) => setAnual(x.filas ?? [])).catch(() => {}) }, [id])
  useEffect(() => { setR(null); pedirSerie(id, VARS, mes, mes).then(setR).catch(() => {}) }, [id, mes])
  const anio = 2000 + Math.floor(mes / 12)
  const clase = anual.find((f) => f.anio === anio)?.clase_condicion ?? null
  return (
    <div>
      {VARS.map((v) => {
        const s = r?.series[v]
        if (!s) return <p key={v}>{nombreVar(v)}: {t('resumen.sinConexion')}</p>
        return <FilaDato key={v} v={v} s={s} mes={mes} />
      })}
      <h3>{t('resumen.condicion')}</h3>
      <p>{clase === null ? t('resumen.lineaBase') : condicion()[clase]} <Chip e="SIMULADO" /></p>
      <h3>{t('resumen.clima')}</h3>
      <p>{d?.clases.length ? [...d.clases].sort((a, b) => b.fraccion - a.fraccion).slice(0, 3).map((c) => `${KOPPEN[Number(c.clase) - 1] ?? c.clase} ${(c.fraccion * 100).toFixed(0)} %`).join(' · ') : t('resumen.sinClase')} <Chip e="REAL·contexto" /></p>
      <h3>{t('resumen.eventos')}</h3>
      <ul>{d?.eventos.length ? d.eventos.map((e) => <li key={e.id}>{e.tipo} {e.inicio}–{e.fin} <Chip e={e.etiqueta} /></li>) : <li>{t('resumen.ninguno')}</li>}</ul>
    </div>
  )
}

// Una fila de variable; un par (variable, unidad) sin conversión se muestra como estado de error, nunca el número crudo
export function FilaDato({ v, s, mes }: { v: string; s: SerieVar; mes: number }) {
  const k = (x: number | null | undefined) => paraMostrar(v, x, s.unidad_medida, mes)
  let x: number | null, unidad: string, lo: number | null, hi: number | null
  try { ({ valor: x, unidad } = k(s.valor[0])); lo = k(s.p10?.[0]).valor; hi = k(s.p90?.[0]).valor } catch {
    return <div className="dato" role="alert"><span>{nombreVar(v)}</span><strong>{t('unidad.sinConversion')}: {v}/{String(s.unidad_medida)}</strong></div>
  }
  const banderas = rotulosDeVariable(v, Math.max(0, s.bandera[0]), x !== null)
  const nota = x === null ? (banderas.join(', ') || (s.bandera[0] < 0 ? t('resumen.sinRegistro') : t('resumen.hueco')))
    : lo != null && hi != null ? `${t('resumen.rango')} ${num(lo)}–${num(hi)}` : `${t('resumen.sinIntervalo')}${banderas.length ? ' · ' + banderas.join(', ') : ''}`
  return (
    <div className="dato">
      <span>{nombreVar(v)} <Chip e="SIMULADO" /></span>
      <strong>{x === null ? t('comun.sinDato') : num(x)} <small>{unidad}</small></strong>
      <small>{nota}</small>
    </div>
  )
}
