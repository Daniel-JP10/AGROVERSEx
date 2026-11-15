// asistido por SI: Claude Code (Anthropic), compromisos del frente presentados con los textos del gemelo, nunca como solución óptima
import { t } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'
import type { Compromisos as TCompromisos, EstrategiaGemelo } from './gemelo'

const GRUPOS: ['gana' | 'cede' | 'similar', ClaveTexto][] = [['gana', 'rotaciones.gana'], ['cede', 'rotaciones.cede'], ['similar', 'rotaciones.similar']]

export function Compromisos({ frente, compromisos }: { frente: EstrategiaGemelo[]; compromisos: TCompromisos }) {
  return (
    <section className="compromisos" aria-labelledby="h-compromisos">
      <h2 id="h-compromisos">{t('rotaciones.compromisos')}</h2>
      <ul>{compromisos.explicacion.map((x) => <li key={x} data-texto-gemelo="">{x}</li>)}</ul>
      {frente.map((e) => e.frente_a_linea_base && (
        <article key={e.id}>
          <h3>{`${e.nombre} (${e.id})`}</h3>
          {GRUPOS.map(([g, clave]) => e.frente_a_linea_base![g].length > 0 && (
            <div key={g}>
              <h4>{t(clave)}</h4>
              <ul>{e.frente_a_linea_base![g].map((x) => <li key={x} data-texto-gemelo="">{x}</li>)}</ul>
            </div>
          ))}
        </article>
      ))}
    </section>
  )
}
