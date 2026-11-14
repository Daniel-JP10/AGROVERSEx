// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useMemo, useState } from 'react'
import { adaptar, type RespRotaciones } from './datos'
import { ordenar, sensibilidad, type Pesos, type Restricciones } from './ordenar'
import { Prioridades } from './Prioridades'
import { TarjetaEstrategia } from './TarjetaEstrategia'

const P0: Pesos = { agua: 0, forraje: 0, nitrogeno: 0, erosion: 0, materiaOrganica: 0, mercado: 0 }
const R0: Restricciones = { cultivosAceptados: null, aguaMaxMm: null, siembraDirecta: true, cosechaForraje: true }
const ROLES = ['habitual', 'alternativa 1', 'alternativa 2']

export function Rotaciones({ resp }: { resp: RespRotaciones }) {
  const [pesos, setPesos] = useState(P0)
  const [rest, setRest] = useState(R0)
  const d = useMemo(() => adaptar(resp), [resp])
  const lista = useMemo(() => ordenar(d.estrategias, pesos, rest), [d, pesos, rest])
  const sens = useMemo(() => sensibilidad(d.estrategias, pesos), [d, pesos])
  if (d.vacio) return <section className="comparador"><p>Sin sistema de rotación documentado para esta unidad en la demo: {d.motivo}.</p></section>
  return (
    <section className="comparador" aria-label="Comparador de rotaciones">
      <h2>Rotaciones: {d.region} <span className="etiqueta" data-testid="etiqueta">{d.etiqueta}</span></h2>
      {d.chino && <p className="nota">Procedencia china (D-009): las filas dependen de un mapa de un grupo chino.</p>}
      <Prioridades pesos={pesos} onPesos={setPesos} rest={rest} onRest={setRest} />
      <p data-testid="sens">Primer lugar {sens.primeroEstable ? 'estable' : 'no estable'} dentro de los intervalos. Cambio mínimo de un peso para cambiarlo: {Object.entries(sens.cambioMinimoPorPeso).filter(([, v]) => v !== null).map(([k, v]) => `${k} ${v}`).join(', ') || 'ninguno'}.</p>
      {lista.map((o) => <TarjetaEstrategia key={o.estrategia.id} o={o} d={d} rol={ROLES[Number(o.estrategia.id.split('-').pop())]} />)}
      {d.pendientes.map((p) => <article key={p} className="tarjeta pendiente" data-testid="pendiente"><h3>{p}: PENDIENTE</h3><p>Sin estrategia con evidencia; no se rellena.</p></article>)}
    </section>
  )
}
