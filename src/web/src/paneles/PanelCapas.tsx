// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEstado } from '../app/estado'
import { Filtros } from './filtros/Filtros'
import { Fuentes } from './Fuentes'
import { CAPAS, TEMAS, TEMA_CLAVE } from '../datos/capas'
import { t } from '../textos/i18n'

// Capas: variable del mapa por tema y opacidad de la coropleta. Filtros: ver filtros/Filtros.tsx.
export function PanelCapas({ herramienta }: { herramienta: string }) {
  const opacidad = useEstado((s) => s.opacidad)
  const setOpacidad = useEstado((s) => s.setOpacidad)
  const capa = useEstado((s) => s.capa)
  const setCapa = useEstado((s) => s.setCapa)
  if (herramienta === 'capas') return (
    <aside className="panel panel-herr" aria-label={t('capas.titulo')}>
      <h2>{t('capas.titulo')}</h2>
      {TEMAS.map((tema) => (
        <fieldset key={tema} className="grupo-capas">
          <legend>{t(TEMA_CLAVE[tema])}</legend>
          {CAPAS.filter((c) => c.tema === tema).map((c) => (
            <label key={c.id} className="capa">
              <input type="radio" name="capa" value={c.id} checked={capa === c.id} onChange={() => setCapa(c.id)} /> {c.nombre}
            </label>
          ))}
        </fieldset>
      ))}
      <label htmlFor="op-coropleta">{t('capas.opacidad')} {opacidad} %</label>
      <input id="op-coropleta" type="range" min={0} max={100} step={1} value={opacidad}
        aria-valuetext={`${opacidad} ${t('capas.porCiento')}`} onChange={(e) => setOpacidad(Number(e.target.value))} />
    </aside>
  )
  if (herramienta === 'filtros') return <Filtros />
  if (herramienta === 'fuentes') return <aside className="panel panel-herr" aria-label={t('capas.fuentes')}><h2>{t('capas.fuentes')}</h2><Fuentes /></aside>
  return null
}
