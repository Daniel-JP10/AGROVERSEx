// asistido por SI: Claude Code (Anthropic), compromisos del frente presentados con los textos del gemelo, nunca como solución óptima
import { t } from '../../textos/i18n'
import { useModo } from '../../textos/modos'
import type { ClaveTexto } from '../../textos/en'
import type { Compromisos as TCompromisos, EstrategiaGemelo } from './gemelo'

const GRUPOS: ['gana' | 'cede' | 'similar', ClaveTexto][] = [['gana', 'rotaciones.gana'], ['cede', 'rotaciones.cede'], ['similar', 'rotaciones.similar']]

export function Compromisos({ frente, compromisos }: { frente: EstrategiaGemelo[]; compromisos: TCompromisos }) {
  // Las cifras de compromiso son medias del ensamble sin rango: al agricultor no se le muestran (AGENTS §4)
  useModo() // suscripción: repinta al cambiar de modo
  const modo = useModo.getState().modo // estado actual (en render estático el hook da el inicial)
  if (modo !== 'tecnico') return (
    <section className="compromisos" aria-labelledby="h-compromisos">
      <h2 id="h-compromisos">{t('rotaciones.compromisos')}</h2>
      <p className="sin-dato">{t('rotaciones.compromisos_tecnico')}</p>
    </section>
  )
  return (
    <section className="compromisos" aria-labelledby="h-compromisos">
      <h2 id="h-compromisos">{t('rotaciones.compromisos')}</h2>
      <p className="sin-dato">{t('rotaciones.compromisos_tecnico')}</p>
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
