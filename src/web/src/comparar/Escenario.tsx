// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { useEstado } from '../app/estado'
import { pedirSerie, mmPorMes } from '../datos/series'
import { limitarEscenario, percentil } from './sincronia'

interface Rango { p25: number; p75: number; min: number; max: number }
const VARS = [
  { id: 'precip', nombre: 'Lluvia', unidad: 'mm/mes', conv: mmPorMes },
  { id: 't2m', nombre: 'Temperatura', unidad: '°C', conv: (x: number, _mes: number) => x },
]

// p25 y p75 salen de la serie mensual de la unidad (INFERENCIA, 2000-2026). Sin base: el control se desactiva con aviso.
export function Escenario() {
  const sel = useEstado((s) => s.seleccion)
  const [rangos, setRangos] = useState<Record<string, Rango> | null>(null)
  const [error, setError] = useState(false)
  const [vals, setVals] = useState<Record<string, number>>({})
  const [motivos, setMotivos] = useState<Record<string, string | undefined>>({})

  useEffect(() => {
    setRangos(null); setError(false); setVals({}); setMotivos({})
    if (!sel) return
    let vivo = true
    pedirSerie(String(sel.id), VARS.map((v) => v.id)).then((r) => {
      if (!vivo) return
      const out: Record<string, Rango> = {}
      for (const v of VARS) {
        const s = (r.series[v.id]?.valor ?? []).map((x, i) => (x === null ? null : v.conv(x, i)))
        const p25 = percentil(s, 0.25), p75 = percentil(s, 0.75), c = s.filter((x): x is number => x !== null)
        if (p25 !== null && p75 !== null) out[v.id] = { p25, p75, min: Math.min(...c), max: Math.max(...c) }
      }
      if (!Object.keys(out).length) throw new Error('sin datos')
      setRangos(out)
      setVals(Object.fromEntries(Object.entries(out).map(([k, x]) => [k, (x.p25 + x.p75) / 2])))
    }).catch(() => { if (vivo) setError(true) })
    return () => { vivo = false }
  }, [sel])

  return (
    <aside className="panel panel-herr" aria-label="Escenario">
      <h2>Escenario</h2>
      {!sel && <p role="status">Seleccione una unidad en el mapa: el escenario se limita a su p25-p75.</p>}
      {sel && error && <p role="alert">Sin p25-p75 para esta unidad (base de datos no disponible): el control está desactivado.</p>}
      {sel && !error && !rangos && <p role="status">Calculando p25-p75…</p>}
      {sel && rangos && VARS.filter((v) => rangos[v.id]).map((v) => {
        const r = rangos[v.id], valor = vals[v.id] ?? r.p25
        // El deslizador se detiene en el borde y queda el motivo a la vista
        const mover = (x: number) => { const e = limitarEscenario(x, r.p25, r.p75); setVals({ ...vals, [v.id]: e.valor }); const tol = (r.p75 - r.p25) * 1e-3, borde = Math.abs(x - r.p25) < tol || Math.abs(x - r.p75) < tol // el eco del valor ya recortado no borra el aviso
          if (e.bloqueado || !borde) setMotivos((m) => ({ ...m, [v.id]: e.motivo })) }
        return (
          <div key={v.id} className="esc-var">
            <label htmlFor={`esc-${v.id}`}>{v.nombre}: {valor.toFixed(1)} {v.unidad}</label>
            <input id={`esc-${v.id}`} type="range" min={r.min} max={r.max} step="any" value={valor}
              aria-valuetext={`${valor.toFixed(1)} ${v.unidad}`} onChange={(ev) => mover(Number(ev.target.value))} />
            <small>p25 {r.p25.toFixed(1)} · p75 {r.p75.toFixed(1)} {v.unidad} (INFERENCIA, serie mensual 2000-2026)</small>
            {motivos[v.id] && <p role="alert" className="esc-motivo" data-testid={`motivo-${v.id}`}>{motivos[v.id]}</p>}
          </div>
        )
      })}
      <small>SIMULADO · DEMO. Solo modula el efecto de rotación publicado; no recalcula el clima ni escribe nada.</small>
    </aside>
  )
}
