// asistido por SI: Claude Code (Anthropic), vista de El gemelo del lote: cinco variables, ventanas de suelo desnudo y enlace a Rotaciones
import { aHash } from '../../app/ruta'
import { t, useIdioma } from '../../textos/i18n'
import { Grafico, bandaValida } from './Grafico'
import { DIBUJADAS, type Banda, type Estrategia, type Origen } from './tipos'
import './gemelo.css'

// Más de la mitad del mes con suelo desnudo (la variable es la fracción del mes)
const UMBRAL_DESNUDO = 0.5
type Ventana = 'firme' | 'posible' | null
// Firme si la mediana lo dice; posible si solo lo dice el borde alto de la banda
const ventanas = (b: Banda): Ventana[] => b.p50.map((m, i) => (m >= UMBRAL_DESNUDO ? 'firme' : b.p90[i] >= UMBRAL_DESNUDO ? 'posible' : null))
// shortcut: lista de meses separados por coma, sin compactar rangos; compactar si el horizonte pasa de unos pocos años
const meses = (v: Ventana[], tipo: Ventana) => v.flatMap((x, i) => (x === tipo ? [i + 1] : [])).join(', ')
const llenar = (texto: string, vars: Record<string, string>) => texto.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '')

type Props = { origen: Origen; lote?: string; base?: Estrategia; alternativa?: Estrategia }

function Ventanas({ filas }: { filas: { clase: string; nombre: string; banda: Banda }[] }) {
  return (
    <section className="ventanas" aria-labelledby="ventanas-t">
      <h2 id="ventanas-t">{t('gemelo.desnudo_nombre')}</h2>
      <p>{t('gemelo.ventanas_nota')}</p>
      {filas.map((f) => {
        const v = ventanas(f.banda)
        const firmes = meses(v, 'firme'), posibles = meses(v, 'posible')
        return (
          <div key={f.clase} className={`fila-ventanas ${f.clase}`}>
            <div className="tira" aria-hidden="true">
              {v.map((x, i) => <span key={i} {...(x ? { 'data-ventana': x } : {})} />)}
            </div>
            <p>
              {firmes || posibles ? (
                <>
                  {firmes && llenar(t('gemelo.ventanas_meses'), { estrategia: f.nombre, meses: firmes })}{' '}
                  {posibles && llenar(t('gemelo.ventanas_posibles'), { meses: posibles })}
                </>
              ) : llenar(t('gemelo.sin_ventanas'), { estrategia: f.nombre })}
            </p>
          </div>
        )
      })}
    </section>
  )
}

export function GemeloVista({ origen, lote, base, alternativa }: Props) {
  useIdioma()
  const fuentes = [
    base && { clase: 'base' as const, nombre: base.nombre, e: base },
    alternativa && { clase: 'alternativa' as const, nombre: alternativa.nombre, e: alternativa },
  ].filter((x) => !!x)
  const filas = fuentes.flatMap((f) => (bandaValida(f.e.trayectoria_mensual.desnudo) ? [{ clase: f.clase, nombre: f.nombre, banda: f.e.trayectoria_mensual.desnudo }] : []))
  return (
    <main className="seccion gemelo">
      <h1>{t('seccion.gemelo')}</h1>
      <p>{t('gemelo.descripcion')}</p>
      {lote && <p>{t('gemelo.lote')}: <strong>{lote}</strong></p>}
      <p><a className="enlace-rotaciones" href={aHash({ seccion: 'rotaciones', params: lote ? { lote } : {} })}>{t('gemelo.enlace_rotaciones')}</a></p>
      {fuentes.length === 0 ? (
        <p className="sin-dato" role="status">{t('aviso.sin_dato')}</p>
      ) : (
        <>
          <p className="rotulo" data-rotulo={origen}>
            <strong>{origen === 'ejemplo' ? t('aviso.simulado') : t('etiqueta.simulacion_modelo')}</strong>
            {origen === 'ejemplo' && ` · ${t('gemelo.ejemplo_nota')}`}
          </p>
          <ul className="leyenda-estrategias">
            {fuentes.map((f) => <li key={f.clase} className={f.clase}><span className="muestra" aria-hidden="true" /> {t(f.clase === 'base' ? 'gemelo.base' : 'gemelo.alternativa')}: {f.nombre}</li>)}
          </ul>
          <p>{t('gemelo.banda')} {t('gemelo.tiempo')}.</p>
          <div className="graficos">
            {DIBUJADAS.map((v) => <Grafico key={v} variable={v} series={fuentes.map((f) => ({ clase: f.clase, nombre: f.nombre, banda: f.e.trayectoria_mensual[v] }))} />)}
          </div>
          {filas.length > 0 && <Ventanas filas={filas} />}
        </>
      )}
    </main>
  )
}
