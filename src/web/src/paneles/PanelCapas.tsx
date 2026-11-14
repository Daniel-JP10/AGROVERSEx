// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEstado } from '../app/estado'
import { Filtros } from './filtros/Filtros'
import { Fuentes } from './Fuentes'
import { CAPAS, TEMAS } from '../datos/capas'

// Capas: variable del mapa por tema y opacidad de la coropleta. Filtros: ver filtros/Filtros.tsx.
export function PanelCapas({ herramienta }: { herramienta: string }) {
  const opacidad = useEstado((s) => s.opacidad)
  const setOpacidad = useEstado((s) => s.setOpacidad)
  const capa = useEstado((s) => s.capa)
  const setCapa = useEstado((s) => s.setCapa)
  if (herramienta === 'capas') return (
    <aside className="panel panel-herr" aria-label="Capas">
      <h2>Capas</h2>
      {TEMAS.map((t) => (
        <fieldset key={t} className="grupo-capas">
          <legend>{t}</legend>
          {CAPAS.filter((c) => c.tema === t).map((c) => (
            <label key={c.id} className="capa">
              <input type="radio" name="capa" value={c.id} checked={capa === c.id} onChange={() => setCapa(c.id)} /> {c.nombre}
            </label>
          ))}
        </fieldset>
      ))}
      <label htmlFor="op-coropleta">Opacidad de la coropleta: {opacidad} %</label>
      <input id="op-coropleta" type="range" min={0} max={100} step={1} value={opacidad}
        aria-valuetext={`${opacidad} por ciento`} onChange={(e) => setOpacidad(Number(e.target.value))} />
    </aside>
  )
  if (herramienta === 'filtros') return <Filtros />
  if (herramienta === 'fuentes') return <aside className="panel panel-herr" aria-label="Fuentes"><h2>Fuentes</h2><Fuentes /></aside>
  return null
}
