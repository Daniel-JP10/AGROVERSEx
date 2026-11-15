// asistido por SI: Claude Code (Anthropic), sección Ciencia y validación: estructura a la espera de contratos/web_datos.md
import { idioma, t, useIdioma } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'
import { useModo } from '../../textos/modos'
import './ciencia.css'

// Props genéricas: la forma de los archivos de Datos no está fijada, esta sección no carga nada
export type Metrica = { id: string; nombre?: string; valor?: number; unidad?: string; intervalo?: [number, number]; linea_base?: number; n?: number }
export type DatosCiencia = { metricas?: Metrica[]; resolucion_producto?: string }

// Métricas que pide la tarea T-W6 y preguntas registradas en D-006, todas abiertas
const RANURAS = ['suelo_desnudo', 'anomalias', 'escala']
const PREGUNTAS = [1, 2, 3, 4]
const LIMITES = [1, 2, 3, 4, 5]

const fmt = (n: number) => new Intl.NumberFormat(idioma(), { maximumSignificantDigits: 3 }).format(n)
// Sin intervalo, línea base y tamaño de muestra no se muestra ni el valor
const completa = (m?: Metrica): m is Metrica & Required<Pick<Metrica, 'valor' | 'intervalo' | 'linea_base' | 'n'>> =>
  !!m && [m.valor, m.linea_base, m.n].every((v) => Number.isFinite(v)) && Array.isArray(m.intervalo) && m.intervalo.length === 2 && m.intervalo.every((v) => Number.isFinite(v))

const SinDato = () => <span className="sin-dato">{t('aviso.sin_dato')}</span>

function Tarjeta({ m, id }: { m?: Metrica; id: string }) {
  const nombre = RANURAS.includes(id) ? t(`ciencia.metrica_${id}` as ClaveTexto) : (m?.nombre ?? id)
  const ok = completa(m)
  const campos: [string, ClaveTexto, string | null][] = [
    ['valor', 'ciencia.campo_valor', ok ? `${fmt(m.valor)}${m.unidad ? ` ${m.unidad}` : ''}` : null],
    ['intervalo', 'ciencia.campo_intervalo', ok ? `${fmt(m.intervalo[0])} – ${fmt(m.intervalo[1])}` : null],
    ['linea_base', 'ciencia.campo_linea_base', ok ? fmt(m.linea_base) : null],
    ['n', 'ciencia.campo_n', ok ? fmt(m.n) : null],
  ]
  return (
    <article className="metrica" data-metrica={id}>
      <h3>{nombre}</h3>
      <dl>
        {campos.map(([c, clave, v]) => <div key={c} data-campo={c}><dt>{t(clave)}</dt><dd>{v ?? <SinDato />}</dd></div>)}
      </dl>
    </article>
  )
}

export function Ciencia({ metricas = [], resolucion_producto }: DatosCiencia = {}) {
  useIdioma()
  useModo((s) => s.modo) // suscripción: repinta al cambiar de modo
  const modo = useModo.getState().modo
  const ids = [...RANURAS, ...metricas.map((m) => m.id).filter((id) => !RANURAS.includes(id))]
  return (
    <main className="seccion ciencia">
      <h1>{t('seccion.ciencia')}</h1>
      <p>{t('ciencia.descripcion')}</p>
      {!metricas.some(completa) && <p className="sin-dato" role="status">{t('aviso.sin_dato')}</p>}
      <section aria-labelledby="c-metricas">
        <h2 id="c-metricas">{t('ciencia.metricas_titulo')}</h2>
        <p>{t('ciencia.honesta')}</p>
        <div className="metricas">{ids.map((id) => <Tarjeta key={id} id={id} m={metricas.find((m) => m.id === id)} />)}</div>
      </section>
      <section aria-labelledby="c-preguntas">
        <h2 id="c-preguntas">{t('ciencia.preguntas_titulo')}</h2>
        <ul className="preguntas">
          {PREGUNTAS.map((i) => (
            <li key={i} data-pregunta={`PI-D${i}`}>
              <strong>PI-D{i}</strong> {t(`ciencia.pi_d${i}` as ClaveTexto)} <span className="estado">{t('ciencia.estado')}: <span data-estado>{t('ciencia.estado_abierta')}</span></span>
            </li>
          ))}
        </ul>
      </section>
      <section aria-labelledby="c-satelite">
        <h2 id="c-satelite">{t('ciencia.satelite_titulo')}</h2>
        <p>
          {modo === 'tecnico'
            ? t('ciencia.satelite_tecnico').replace('{resolucion_producto}', resolucion_producto ?? t('ciencia.resolucion_pendiente'))
            : t('ciencia.satelite_agricultor')}
        </p>
      </section>
      <section aria-labelledby="c-limites">
        <h2 id="c-limites">{t('ciencia.limites_titulo')}</h2>
        <ul className="limitaciones">
          {LIMITES.map((i) => <li key={i} data-limitacion>{t(`ciencia.limite_${i}` as ClaveTexto)}</li>)}
        </ul>
      </section>
    </main>
  )
}
