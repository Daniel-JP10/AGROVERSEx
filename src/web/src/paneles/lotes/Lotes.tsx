// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { parsearWkt } from '../../datos/wkt'
import { SensorSatelite } from '../../graficos/SensorSatelite'
import { RIESGOS, fechaDia, rotuloRiesgo, ventanaSueloExpuesto, type Lote } from './modelo'
import { Banco } from './Banco'

interface FilaLote { id: string; geom_wkt: string; cultivo_actual: string }
interface Diario { dia_id: number; sm_verdad: number | null; sm_sensor: number | null }
type Resp = { vacio: true; motivo: string } | { vacio: false; lotes: FilaLote[] }

// Mapa mínimo: lotes como GeoJSON propio, dibujados en SVG ajustado a sus polígonos.
function Mapa({ lotes, sel, alElegir }: { lotes: FilaLote[]; sel: string; alElegir: (id: string) => void }) {
  const fs = lotes.flatMap((l) => { try { return [{ id: l.id, p: parsearWkt(l.geom_wkt) }] } catch { return [] } })
  const pts = fs.flatMap((f) => f.p.coordinates[0])
  const [x0, x1] = [Math.min(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[0]))]
  const [y0, y1] = [Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[1]))]
  const k = 280 / Math.max(x1 - x0, y1 - y0, 1e-9)
  return (
    <svg viewBox="0 0 300 300" role="group" aria-label="Mapa de lotes sintéticos" width="300" height="300">
      {fs.map((f) => (
        <polygon key={f.id} data-testid="lote" tabIndex={0} role="button" aria-label={`Lote ${f.id}`} aria-pressed={f.id === sel}
          points={f.p.coordinates[0].map(([x, y]: number[]) => `${10 + (x - x0) * k},${290 - (y - y0) * k}`).join(' ')}
          fill={f.id === sel ? '#d97706' : '#4b8f6b'} stroke="#222" strokeWidth={f.id === sel ? 2 : 1}
          onClick={() => alElegir(f.id)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') alElegir(f.id) }} />
      ))}
    </svg>
  )
}

export function Lotes({ id }: { id: string }) {
  const [r, setR] = useState<Resp | null>(null)
  const [sel, setSel] = useState('')
  const [det, setDet] = useState<{ lote: FilaLote; diario: Diario[]; ventanas: Lote['ventanas'] } | null>(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    setR(null); setErr('')
    fetch(`/api/lotes/${encodeURIComponent(id)}`).then((x) => x.json()).then((j) => { setR(j); if (!j.vacio) setSel(j.lotes[0].id) }).catch(() => setErr('No se pudieron cargar los lotes'))
  }, [id])
  useEffect(() => {
    if (!sel) return
    setDet(null)
    fetch(`/api/lote/${encodeURIComponent(sel)}`).then((x) => x.json()).then(setDet).catch(() => setErr('No se pudo cargar el lote'))
  }, [sel])
  if (err) return <p role="alert">{err}</p>
  if (!r) return <p role="status">Cargando…</p>
  if (r.vacio) return <p>Los lotes solo existen en zonas DEMO: {r.motivo}.</p>
  const v = det && ventanaSueloExpuesto(det)
  const ult = det ? det.diario.slice(-365) : []
  return (
    <div>
      <p className="etiqueta" data-testid="aviso-sim">SIMULADO · DEMO · lotes sintéticos, sin persona ni finca real</p>
      <Mapa lotes={r.lotes} sel={sel} alElegir={setSel} />
      {det && <>
        <h3>Lote {det.lote.id} · {det.lote.cultivo_actual}</h3>
        <h3>Ventana de suelo expuesto</h3>
        <p data-testid="ventana">{v ? `${fechaDia(v.inicio)} a ${fechaDia(v.fin)} · error ±${v.errorSemanas.toFixed(1)} semanas · SIMULADO` : 'Sin detección (SIMULADO)'}</p>
        <h3>Sensor frente a verdad simulada</h3>
        <SensorSatelite dias={ult.map((d) => d.dia_id)} sensor={ult.map((d) => d.sm_sensor)} verdad={ult.map((d) => d.sm_verdad)} />
        <p className="etiqueta">SIMULADO · DEMO · «verdad simulada» es la humedad real del simulador (sm_verdad), no una observación de satélite · huecos sin interpolar</p>
        <h3>Vulnerabilidades</h3>
        <ul>{Object.values(RIESGOS).map((x) => (
          <li key={x.id} data-testid="riesgo"><strong>{x.nombre}</strong>: {x.valor ?? 'sin dato'} · {rotuloRiesgo(x)} · <small>{x.nota}</small></li>
        ))}</ul>
      </>}
      <Banco />
    </div>
  )
}
