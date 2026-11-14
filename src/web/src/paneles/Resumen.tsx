// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { clienteDefecto } from '../datos/consultas'
import { pedirSerie, nombreVar, type RespSerie } from '../datos/series'
import { paraMostrar } from '../comun/unidades'
import { rotulosDeVariable } from '../datos/banderas'
import { useEstado } from '../app/estado'
import type { DetalleUnidad } from '../datos/tipos'
import { Chip } from './Chip'
import { t } from '../textos/i18n'

const VARS = ['precip', 't2m', 'ndvi']
// Clases 1 a 30 de Beck et al. 2023 (legend.txt)
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
        const k = (x: number | null | undefined) => paraMostrar(v, x, s.unidad_medida, mes)
        const { valor: x, unidad } = k(s.valor[0]), lo = k(s.p10?.[0]).valor, hi = k(s.p90?.[0]).valor
        const banderas = rotulosDeVariable(v, Math.max(0, s.bandera[0]), x !== null)
        const nota = x === null ? (banderas.join(', ') || (s.bandera[0] < 0 ? t('resumen.sinRegistro') : t('resumen.hueco')))
          : lo != null && hi != null ? `${t('resumen.rango')} ${num(lo)}–${num(hi)}` : `${t('resumen.sinIntervalo')}${banderas.length ? ' · ' + banderas.join(', ') : ''}`
        return (
          <div className="dato" key={v}>
            <span>{nombreVar(v)} <Chip e="SIMULADO" /></span>
            <strong>{x === null ? t('comun.sinDato') : num(x)} <small>{unidad}</small></strong>
            <small>{nota}</small>
          </div>
        )
      })}
      <h3>{t('resumen.condicion')}</h3>
      <p>{clase === null ? t('resumen.lineaBase') : condicion()[clase]} <Chip e="SIMULADO" /></p>
      <h3>{t('resumen.eventos')}</h3>
      <ul>{d?.eventos.length ? d.eventos.map((e) => <li key={e.id}>{e.tipo} {e.inicio}–{e.fin} <Chip e={e.etiqueta} /></li>) : <li>{t('resumen.ninguno')}</li>}</ul>
    </div>
  )
}
