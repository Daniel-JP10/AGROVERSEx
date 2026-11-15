// asistido por SI: Claude Code (Anthropic), compromisos del frente presentados con los textos del gemelo, nunca como solución óptima
import { idioma, t } from '../../textos/i18n'
import { nombreEstrategia } from '../lote/datos'
import { useModo } from '../../textos/modos'
import type { ClaveTexto } from '../../textos/en'
import type { Compromisos as TCompromisos, EstrategiaGemelo, Objetivo } from './gemelo'
import { traducir, type Catalogo } from './textosGemelo'

// Las líneas del paquete vienen en español ("<objetivo>: a -> b"): con catálogo se cambia solo el nombre del objetivo, las cifras quedan iguales
export function lineaObjetivo(s: string, objetivos: Objetivo[], cat?: Catalogo): string {
  if (!cat) return s
  const o = objetivos.find((x) => x.texto_clave && s.startsWith(`${x.texto}:`))
  return o ? `${traducir(cat, o.texto_clave!)}${s.slice(o.texto.length)}` : s
}

const GRUPOS: ['gana' | 'cede' | 'similar', ClaveTexto][] = [['gana', 'rotaciones.gana'], ['cede', 'rotaciones.cede'], ['similar', 'rotaciones.similar']]

export function Compromisos({ frente, compromisos, objetivos = [], catalogo }: { frente: EstrategiaGemelo[]; compromisos: TCompromisos; objetivos?: Objetivo[]; catalogo?: Catalogo }) {
  const explicacion = catalogo && compromisos.explicacion_claves?.length ? compromisos.explicacion_claves.map((x) => traducir(catalogo, x.clave, x.parametros)) : compromisos.explicacion
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
      <ul>{explicacion.map((x) => <li key={x} data-texto-gemelo="">{x}</li>)}</ul>
      {frente.map((e) => e.frente_a_linea_base && (
        <article key={e.id}>
          <h3>{`${idioma() === 'en' ? nombreEstrategia(e) : e.nombre} (${e.id})`}</h3>
          {GRUPOS.map(([g, clave]) => e.frente_a_linea_base![g].length > 0 && (
            <div key={g}>
              <h4>{t(clave)}</h4>
              <ul>{e.frente_a_linea_base![g].map((x) => <li key={x} data-texto-gemelo="">{lineaObjetivo(x, objetivos, catalogo)}</li>)}</ul>
            </div>
          ))}
        </article>
      ))}
    </section>
  )
}
