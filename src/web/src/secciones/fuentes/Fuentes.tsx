// asistido por SI: Claude Code (Anthropic), sección Fuentes: glosario por modo, créditos generados y declaración de uso de SI; tres columnas de hoja y créditos de la fase 3; registros en inglés en modo EN (D-043)
import { Relleno } from '../../app/Relleno'
import { TERMINOS } from '../../textos/glosario'
import { dato, rellenar, type Resolver } from '../../textos/huecos'
import { t, useIdioma } from '../../textos/i18n'
import { useModo, type Modo } from '../../textos/modos'
import { CITAS, CITAS_EN, LICENCIAS, LICENCIAS_EN, USO_SI, type Tabla } from './tablas'

// Columnas de los registros que no aportan al crédito público
const OMITIR = new Set(['Quién lo agregó', 'Fecha', 'Added by', 'Date'])
const ES_URL = /^https?:\/\/\S+$/

// `modo` solo se pasa en pruebas: el render de servidor no ve los cambios del almacén
export function Glosario({ resolver = dato, modo: forzado }: { resolver?: Resolver; modo?: Modo }) {
  useIdioma()
  const delAlmacen = useModo((s) => s.modo)
  const modo = forzado ?? delAlmacen
  return (
    <dl className="glosario">
      {TERMINOS.map(({ id, fuente, url }) => {
        const tecnico = t(`glosario.${id}.tecnico`)
        const pendiente = modo === 'tecnico' && rellenar(tecnico, resolver).faltan.length > 0
        return (
          <div key={id}>
            <dt>{t(`glosario.${id}.nombre`)}</dt>
            <dd>
              <p>{t(`glosario.${id}.agricultor`)}</p>
              {modo === 'tecnico' && <p className="tecnico"><Relleno texto={tecnico} resolver={resolver} /></p>}
              {pendiente && <p className="sin-dato">{t('aviso.sin_dato')}</p>}
              <small>{t('fuentes.fuente')}: <cite>{url ? <a href={url} rel="noreferrer">{t(fuente)}</a> : t(fuente)}</cite></small>
            </dd>
          </div>
        )
      })}
    </dl>
  )
}

function TablaCredito({ tabla, abierta }: { tabla: Tabla; abierta: boolean }) {
  const cols = tabla.columnas.map((c, i) => i).filter((i) => !OMITIR.has(tabla.columnas[i]))
  return (
    <details data-credito="" open={abierta}>
      <summary>{tabla.titulo}</summary>
      <div className="tabla-scroll">
        <table data-tabla="">
          <thead><tr>{cols.map((i) => <th key={i} scope="col">{tabla.columnas[i]}</th>)}</tr></thead>
          <tbody>
            {tabla.filas.map((f, n) => (
              <tr key={n} data-fila="">{cols.map((i) => <td key={i}>{ES_URL.test(f[i]) ? <a href={f[i]} rel="noreferrer">{f[i]}</a> : f[i]}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

export function Creditos() {
  // D-043: el registro inglés en modo EN, el canónico en español en modo ES
  const [lic, cit] = useIdioma() === 'en' ? [LICENCIAS_EN, CITAS_EN] : [LICENCIAS, CITAS]
  return (
    <div>
      <p>{t('fuentes.creditos_nota')}</p>
      {lic.map((tb, i) => <TablaCredito key={tb.titulo} tabla={tb} abierta={i === 0} />)}
      {cit.map((tb) => <TablaCredito key={tb.titulo} tabla={tb} abierta />)}
    </div>
  )
}

export function DeclaracionSI() {
  useIdioma()
  return (
    <div data-testid="declaracion-si">
      <p>{t('fuentes.si_texto')}</p>
      <ul>
        {USO_SI.map((f) => (
          <li key={f.herramienta}><Relleno texto={t('fuentes.si_fila')} resolver={(n) => (n === 'herramienta' ? f.herramienta : n === 'archivos' ? String(f.archivos) : undefined)} /></li>
        ))}
      </ul>
    </div>
  )
}

// Tres columnas de tarjetas hoja: fuentes, glosario y créditos (plan v1 §b, v2 §6); el modo se elige en la cabecera
export function Fuentes() {
  useIdioma()
  return (
    <main className="seccion fuentes">
      <h1>{t('seccion.fuentes')}</h1>
      <p>{t('fuentes.f.intro')}</p>
      <div className="columnas-fuentes">
        <section className="tarjeta-hoja" aria-labelledby="f-fuentes">
          <h2 id="f-fuentes">{t('fuentes.f.fuentes')}</h2>
          <Creditos />
        </section>
        <section className="tarjeta-hoja" aria-labelledby="f-glosario">
          <h2 id="f-glosario">{t('fuentes.f.glosario')}</h2>
          <Glosario />
        </section>
        <section className="tarjeta-hoja" aria-labelledby="creditos">
          <h2 id="creditos">{t('fuentes.f.creditos')}</h2>
          {(['fuentes.f.credito_director', 'fuentes.f.credito_diseno', 'fuentes.f.credito_gemelo'] as const).map((k) => <p key={k} data-credito-equipo="">{t(k)}</p>)}
          <p data-referencias-ia="">{t('fuentes.f.referencias_ia')}</p>
          <h3>{t('fuentes.si_titulo')}</h3>
          <DeclaracionSI />
        </section>
      </div>
    </main>
  )
}
