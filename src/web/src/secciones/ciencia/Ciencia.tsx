// asistido por SI: Claude Code (Anthropic), sección Ciencia y validación: una tarjeta por afirmación con cifra, intervalo, periodo, fuente y etiqueta (plan v2 §6)
import type { ReactNode } from 'react'
import { idioma, t, useIdioma, type ClaveTodo } from '../../textos/i18n'
import { ARCHIVOS, PI_D1_MUNDO, bandaHls, erosion, estacion, hls, lluvia2026, piD1, rangoPiD1Mundo, temperatura, type InformePiD1Mundo } from './datos'
import './ciencia.css'

type Etiqueta = 'FUENTE' | 'INFERENCIA'

// Formatos según el idioma activo; las cifras vienen de datos.ts
const fmt = (o: Intl.NumberFormatOptions) => (x: number) => new Intl.NumberFormat(idioma(), o).format(x)
const num = (x: number, d = 2) => fmt({ maximumFractionDigits: d, minimumFractionDigits: d })(x)
const firmado = (x: number, d = 2) => fmt({ maximumFractionDigits: d, minimumFractionDigits: d, signDisplay: 'always' })(x)
const pct = (x: number) => fmt({ style: 'percent', maximumFractionDigits: 1, minimumFractionDigits: 1 })(x)
const pctFirmado = (x: number) => fmt({ style: 'percent', maximumFractionDigits: 1, minimumFractionDigits: 1, signDisplay: 'always' })(x)
const entero = (x: number) => fmt({})(x)
// Mes "aaaa-mm" con su nombre en el idioma activo
const nombreMes = (m: string) => new Date(`${m}-15T00:00:00Z`).toLocaleDateString(idioma(), { month: 'long', year: 'numeric', timeZone: 'UTC' })

/** Texto de una clave con sus huecos {x} llenos; un hueco sin valor queda visible para que la prueba lo detecte. */
export const f = (clave: ClaveTodo, v: Record<string, string | number>) => t(clave).replace(/\{(\w+)\}/g, (m, k: string) => (k in v ? String(v[k]) : m))

const NoDisponible = () => <span className="sin-dato">{t('ciencia.c.no_disponible')}</span>
const Lineas = ({ textos }: { textos: string[] }) => <>{textos.map((x) => <span key={x} className="linea">{x}</span>)}</>

function Tarjeta({ id, titulo, cifra, intervalo, periodo, fuente, etiqueta, nota, children }: {
  id: string; titulo: ClaveTodo | { texto: string }; cifra: ReactNode; intervalo: ReactNode; periodo: ReactNode; fuente: string | null; etiqueta: Etiqueta | null; nota?: ReactNode; children?: ReactNode
}) {
  return (
    <article className="tarjeta-hoja" data-tarjeta={id}>
      <h2>{typeof titulo === 'string' ? t(titulo) : titulo.texto}</h2>
      {children}
      <dl>
        <div data-campo="cifra"><dt>{t('ciencia.c.cifra')}</dt><dd>{cifra ?? <NoDisponible />}</dd></div>
        <div data-campo="intervalo"><dt>{t('ciencia.c.intervalo')}</dt><dd>{intervalo ?? <NoDisponible />}</dd></div>
        <div data-campo="periodo"><dt>{t('ciencia.c.periodo')}</dt><dd>{periodo ?? <NoDisponible />}</dd></div>
        <div data-campo="fuente"><dt>{t('ciencia.c.fuente')}</dt><dd>{fuente ? <code>{fuente}</code> : <NoDisponible />}</dd></div>
        <div data-campo="etiqueta"><dt>{t('ciencia.c.etiqueta')}</dt><dd>{etiqueta ? <span className="etiqueta-evidencia" data-etiqueta={etiqueta}>{t(`ciencia.c.tag.${etiqueta}`)}</span> : <NoDisponible />}</dd></div>
      </dl>
      {nota && <p className="nota">{nota}</p>}
    </article>
  )
}

// Barras de la fracción de vistas despejadas por mes, con la banda del percentil bajo al alto
function GraficoHls({ lote, meses, periodo }: (typeof hls)[number]) {
  const w = 360, h = 72, paso = w / meses.length
  const y = (v: number) => h - v * h
  return (
    <svg className="grafico-hls" viewBox={`0 0 ${w} ${h + 2}`} role="img" aria-label={f('ciencia.c.hls.grafico', { lote, desde: periodo[0], hasta: periodo[1] })}>
      <line className="eje" x1={0} y1={h} x2={w} y2={h} />
      {meses.map((m, i) => (
        <g key={m.mes}>
          <rect className="barra" x={i * paso + 1} y={y(m.media)} width={paso - 2} height={h - y(m.media)} />
          <line className="banda" x1={i * paso + paso / 2} x2={i * paso + paso / 2} y1={y(m.q95)} y2={y(m.q05)} />
        </g>
      ))}
    </svg>
  )
}

/** PI-D1 mundial: oculto con "Not available yet" mientras no se pase el informe verificado (plan v2 §7). */
export function TarjetaPiD1Mundo({ informe = PI_D1_MUNDO }: { informe?: InformePiD1Mundo | null }) {
  const r = rangoPiD1Mundo(informe)
  return (
    <Tarjeta id="pi_d1_mundo" titulo="ciencia.c.pid1m.titulo" etiqueta={r ? 'FUENTE' : null} fuente={r ? ARCHIVOS.piD1Mundo : null}
      cifra={r ? f('ciencia.c.pid1m.cifra', { min: num(r.min * 100, 1), max: num(r.max * 100, 1) }) : null}
      intervalo={null} periodo={null} />
  )
}

export function Ciencia() {
  useIdioma()
  const c = temperatura.corregida, b = temperatura.cruda
  return (
    <main className="seccion ciencia">
      <h1>{t('marco.nav.ciencia')}</h1>
      <p>{t('ciencia.c.intro')}</p>
      <div className="tarjetas">
        <Tarjeta id="estacion" titulo="ciencia.c.estacion.titulo" etiqueta={estacion ? 'FUENTE' : null} fuente={estacion ? ARCHIVOS.estacion : null}
          cifra={estacion && f('ciencia.c.estacion.cifra', { power: pctFirmado(estacion.power), imerg: pctFirmado(estacion.imerg) })}
          intervalo={null}
          periodo={estacion && f('ciencia.c.estacion.periodo', { desde: estacion.periodo[0], hasta: estacion.periodo[1], dias: entero(estacion.dias), fraccion: pct(estacion.fraccion) })}
          nota={t('ciencia.c.aviso_nc')} />

        <Tarjeta id="temperatura" titulo="ciencia.c.temp.titulo" etiqueta="FUENTE" fuente={ARCHIVOS.temperatura}
          cifra={f('ciencia.c.temp.cifra', { sesgo: firmado(c.sesgo), mae: num(c.mae), sesgo0: firmado(b.sesgo) })}
          intervalo={f('ciencia.c.temp.intervalo', { sa: firmado(c.sesgoIc[0]), sb: firmado(c.sesgoIc[1]), ma: num(c.maeIc[0]), mb: num(c.maeIc[1]), ba: firmado(b.sesgoIc[0]), bb: firmado(b.sesgoIc[1]), nivel: temperatura.nivel })}
          periodo={f('ciencia.c.temp.periodo', { desde: temperatura.periodo[0], hasta: temperatura.periodo[1], n: entero(c.n), fraccion: pct(c.fraccion) })}
          nota={t('ciencia.c.aviso_nc')} />

        <Tarjeta id="hls" titulo="ciencia.c.hls.titulo" etiqueta="FUENTE" fuente={ARCHIVOS.hls}
          cifra={<Lineas textos={hls.map((l) => f('ciencia.c.hls.cifra', { lote: l.lote, mediana: pct(l.mediana) }))} />}
          intervalo={<Lineas textos={hls.map((l) => f('ciencia.c.hls.intervalo', { lote: l.lote, min: pct(l.min), max: pct(l.max), n: l.meses.length, bajo: bandaHls.bajo, alto: bandaHls.alto }))} />}
          periodo={f('ciencia.c.hls.periodo', { desde: hls[0].periodo[0], hasta: hls[0].periodo[1] })}>
          {hls.map((l) => <GraficoHls key={l.lote} {...l} />)}
        </Tarjeta>

        <Tarjeta id="lluvia_2026" titulo={{ texto: f('ciencia.c.lluvia.titulo', { meses: f('ciencia.c.y', { a: nombreMes(lluvia2026[0].mes), b: nombreMes(lluvia2026[1].mes) }) }) }} etiqueta="INFERENCIA" fuente={ARCHIVOS.s4}
          cifra={<Lineas textos={lluvia2026.map((m) => f('ciencia.c.lluvia.cifra', { mes: m.mes, razon: num(m.imerg.razon), razon_power: num(m.power.razon) }))} />}
          intervalo={<Lineas textos={lluvia2026.map((m) => f('ciencia.c.lluvia.intervalo', { mes: m.mes, late: num(m.imerg.late_mm_dia, 1), min: num(m.imerg.final_min, 1), max: num(m.imerg.final_max, 1) }))} />}
          periodo={f('ciencia.c.lluvia.periodo', { n: Math.min(...lluvia2026.map((m) => m.imerg.n_clim)) })} />

        <Tarjeta id="pi_d1_colombia" titulo="ciencia.c.pid1.titulo" etiqueta="FUENTE" fuente={ARCHIVOS.piD1}
          cifra={<Lineas textos={piD1.map((v) => f('ciencia.c.pid1.cifra', { variable: t(`ciencia.c.pid1.var.${v.variable}`), f_alto: pct(v.alto.fraccion), u_alto: v.alto.umbral, f_bajo: pct(v.bajo.fraccion), u_bajo: v.bajo.umbral }))} />}
          intervalo={t('ciencia.c.pid1.intervalo')}
          periodo={f('ciencia.c.pid1.periodo', { desde: piD1[0].meses[0], hasta: piD1[0].meses[piD1[0].meses.length - 1], n: entero(piD1[0].n) })}
          nota={t('ciencia.c.pid1.nota')} />

        <TarjetaPiD1Mundo />

        <Tarjeta id="erosion" titulo="ciencia.c.erosion.titulo" etiqueta="INFERENCIA" fuente={ARCHIVOS.erosion}
          cifra={<Lineas textos={erosion.map((l) => f('ciencia.c.erosion.cifra', { lote: l.lote, base: num(l.base) }))} />}
          intervalo={<Lineas textos={erosion.map((l) => f('ciencia.c.erosion.intervalo', { lote: l.lote, min: num(Math.min(l.base, l.imerg)), max: num(Math.max(l.base, l.imerg)), imerg: num(l.imerg), p10: num(l.pendiente[0], 3), p90: num(l.pendiente[2], 3) }))} />}
          periodo={f('ciencia.c.hls.periodo', { desde: erosion[0].periodo[0], hasta: erosion[0].periodo[1] })}
          nota={t('ciencia.c.erosion.nota')} />

        <Tarjeta id="confianza" titulo="ciencia.c.confianza.titulo" etiqueta={null} fuente={null} cifra={null} intervalo={null} periodo={null} />
      </div>
      <section className="tarjeta-hoja limites" aria-labelledby="c-limites">
        <h2 id="c-limites">{t('ciencia.c.limites')}</h2>
        <ul>
          <li>{t('ciencia.c.limite_radiacion')}</li>
          {(['ciencia.limite_1', 'ciencia.limite_2', 'ciencia.limite_3', 'ciencia.limite_5'] as const).map((k) => <li key={k}>{t(k)}</li>)}
        </ul>
        <p>{t('ciencia.satelite_agricultor')}</p>
      </section>
    </main>
  )
}
