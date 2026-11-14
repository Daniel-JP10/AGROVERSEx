// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { clienteDefecto } from '../datos/consultas'
import { pedirSerie, paraMostrar, nombreVar, type RespSerie } from '../datos/series'
import { rotulosDeVariable } from '../datos/banderas'
import { useEstado } from '../app/estado'
import type { DetalleUnidad } from '../datos/tipos'
import { Chip } from './Chip'

const VARS = ['precip', 't2m', 'ndvi']
// Clases 1 a 30 de Beck et al. 2023 (legend.txt)
const KOPPEN = 'Af Am Aw BWh BWk BSh BSk Csa Csb Csc Cwa Cwb Cwc Cfa Cfb Cfc Dsa Dsb Dsc Dsd Dwa Dwb Dwc Dwd Dfa Dfb Dfc Dfd ET EF'.split(' ')
const CONDICION = ['degradada', 'estable', 'en mejora']
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
        if (!s) return <p key={v}>{nombreVar(v)}: sin conexión</p>
        const k = (x: number | null | undefined) => paraMostrar(v, x, s.unidad_medida, mes)
        const { valor: x, unidad } = k(s.valor[0]), lo = k(s.p10?.[0]).valor, hi = k(s.p90?.[0]).valor
        const banderas = rotulosDeVariable(v, Math.max(0, s.bandera[0]), x !== null)
        const nota = x === null ? (banderas.join(', ') || (s.bandera[0] < 0 ? 'sin registro' : 'hueco'))
          : lo != null && hi != null ? `rango ${num(lo)}–${num(hi)}` : `sin intervalo en el producto${banderas.length ? ' · ' + banderas.join(', ') : ''}`
        return (
          <div className="dato" key={v}>
            <span>{nombreVar(v)} <Chip e="SIMULADO" /></span>
            <strong>{x === null ? 'sin dato' : num(x)} <small>{unidad}</small></strong>
            <small>{nota}</small>
          </div>
        )
      })}
      <h3>Condición de la tierra</h3>
      <p>{clase === null ? 'línea base (2000-2015): el indicador compara periodos posteriores' : CONDICION[clase]} <Chip e="SIMULADO" /></p>
      <h3>Clima (Köppen)</h3>
      <p>{d?.clases.length ? [...d.clases].sort((a, b) => b.fraccion - a.fraccion).slice(0, 3).map((c) => `${KOPPEN[Number(c.clase) - 1] ?? c.clase} ${(c.fraccion * 100).toFixed(0)} %`).join(' · ') : 'sin clase'} <Chip e="REAL·contexto" /></p>
      <h3>Eventos</h3>
      <ul>{d?.eventos.length ? d.eventos.map((e) => <li key={e.id}>{e.tipo} {e.inicio}–{e.fin} <Chip e={e.etiqueta} /></li>) : <li>ninguno registrado</li>}</ul>
    </div>
  )
}
