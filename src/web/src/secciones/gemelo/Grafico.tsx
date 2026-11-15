// asistido por SI: Claude Code (Anthropic), gráfico SVG de una variable del gemelo con banda p10 a p90 y texto alternativo
import { idioma, t } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'
import { useModo } from '../../textos/modos'
import type { Banda, VariableGemelo } from './tipos'

export type Serie = { clase: 'base' | 'alternativa'; nombre: string; banda?: Banda }

const A = 360, H = 150, IZQ = 44, DER = 8, ARR = 8, ABA = 18

// Solo se dibuja una banda completa y finita: sin p10 y p90 no se muestra ningún valor
export const bandaValida = (b?: Banda): b is Banda => {
  if (!b || !b.p50?.length || b.p10?.length !== b.p50.length || b.p90?.length !== b.p50.length) return false
  return [...b.p10, ...b.p50, ...b.p90].every((v) => typeof v === 'number' && Number.isFinite(v))
}

export const formato = (n: number) => new Intl.NumberFormat(idioma(), { maximumSignificantDigits: 3 }).format(n)
const en = () => idioma() === 'en'
export const unidad = (v: VariableGemelo) => ({ W: 'mm', N: 'kg N/ha', C: 't C/ha', B: en() ? 'kg DM/ha' : 'kg MS/ha', V: en() ? 'fraction' : 'fracción', desnudo: en() ? 'fraction' : 'fracción' })[v]
const llenar = (texto: string, vars: Record<string, string>) => texto.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '')

export function Grafico({ variable, series }: { variable: VariableGemelo; series: Serie[] }) {
  useModo((s) => s.modo) // suscripción: repinta al cambiar de modo
  const modo = useModo.getState().modo
  const validas = series.filter((s): s is Serie & { banda: Banda } => bandaValida(s.banda))
  const nombre = t(`gemelo.${variable}_nombre` as ClaveTexto)
  const frase = t(`gemelo.${variable}_${modo === 'tecnico' ? 'tecnico' : 'agricultor'}` as ClaveTexto)
  if (validas.length === 0) {
    return (
      <figure className="grafico" data-variable={variable}>
        <figcaption><strong>{nombre}</strong> {frase}</figcaption>
        <p className="sin-dato">{t('gemelo.sin_banda')}</p>
      </figure>
    )
  }
  const todos = validas.flatMap((s) => [...s.banda.p10, ...s.banda.p90])
  const lo = Math.min(...todos), hi = Math.max(...todos)
  const n = Math.max(...validas.map((s) => s.banda.p50.length))
  const x = (i: number) => IZQ + (n > 1 ? (i * (A - IZQ - DER)) / (n - 1) : 0)
  const y = (v: number) => ARR + (1 - (v - lo) / (hi - lo || 1)) * (H - ARR - ABA)
  const pts = (v: number[]) => v.map((d, i) => `${x(i).toFixed(1)},${y(d).toFixed(1)}`)
  return (
    <figure className="grafico" data-variable={variable}>
      <figcaption><strong>{nombre}</strong> ({unidad(variable)}) {frase}</figcaption>
      <svg viewBox={`0 0 ${A} ${H}`} role="img" aria-label={`${nombre}: ${t('gemelo.banda')}`}>
        <line className="eje" x1={IZQ} x2={IZQ} y1={ARR} y2={H - ABA} />
        <line className="eje" x1={IZQ} x2={A - DER} y1={H - ABA} y2={H - ABA} />
        <text className="marca" x={IZQ - 4} y={ARR + 8} textAnchor="end">{formato(hi)}</text>
        <text className="marca" x={IZQ - 4} y={H - ABA} textAnchor="end">{formato(lo)}</text>
        <text className="marca" x={IZQ} y={H - 4}>1</text>
        <text className="marca" x={A - DER} y={H - 4} textAnchor="end">{n}</text>
        {validas.map((s) => (
          <g key={s.clase} className={`serie ${s.clase}`}>
            <polygon className="banda" points={[...pts(s.banda.p90), ...pts(s.banda.p10).reverse()].join(' ')} />
            <polyline className="mediana" fill="none" points={pts(s.banda.p50).join(' ')} />
          </g>
        ))}
      </svg>
      <ul className="resumen">
        {validas.map((s) => {
          const f = s.banda.p50.length - 1
          const texto = llenar(t('gemelo.resumen'), {
            estrategia: s.nombre, inicio: formato(s.banda.p50[0]), fin: formato(s.banda.p50[f]),
            bajo: formato(s.banda.p10[f]), alto: formato(s.banda.p90[f]), unidad: unidad(variable),
          })
          return <li key={s.clase}><span data-valor data-p10={s.banda.p10[f]} data-p90={s.banda.p90[f]}>{texto}</span></li>
        })}
      </ul>
    </figure>
  )
}
