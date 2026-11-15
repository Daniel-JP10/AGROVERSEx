// asistido por SI: Claude Code (Anthropic), gráfico SVG de una variable mensual con banda p10 a p90 y eje en años
import { t } from '../../textos/i18n'
import { fmt, llenar } from './datos'

export interface SerieBanda { id: string; nombre: string; p10: number[]; p50: number[]; p90: number[] }

const A = 420, H = 170, IZQ = 48, DER = 10, ARR = 10, ABA = 26

// Solo bandas completas y finitas; sin p10 y p90 no se dibuja ningún valor
export const bandaCompleta = (s: { p10?: unknown[]; p50?: unknown[]; p90?: unknown[] }) =>
  !!s.p50?.length && s.p10?.length === s.p50.length && s.p90?.length === s.p50.length &&
  [...s.p10, ...s.p50, ...s.p90].every((v) => typeof v === 'number' && Number.isFinite(v))

export function GraficoBanda({ titulo, unidad, series, anios }: { titulo: string; unidad: string; series: SerieBanda[]; anios: number }) {
  const validas = series.filter(bandaCompleta)
  if (!validas.length) return <figure className="grafico-banda"><figcaption>{titulo}</figcaption><p className="sin-dato">{t('lote.no_disponible')}</p></figure>
  const todos = validas.flatMap((s) => [...s.p10, ...s.p90])
  const lo = Math.min(0, ...todos), hi = Math.max(...todos)
  const n = validas[0].p50.length
  const x = (i: number) => IZQ + ((i + 0.5) * (A - IZQ - DER)) / n
  const y = (v: number) => ARR + (1 - (v - lo) / (hi - lo || 1)) * (H - ARR - ABA)
  const pts = (v: number[]) => v.map((d, i) => `${x(i).toFixed(1)},${y(d).toFixed(1)}`)
  const ancho = (A - IZQ - DER) / anios
  return (
    <figure className="grafico-banda">
      <figcaption><strong>{titulo}</strong> ({unidad})</figcaption>
      <svg viewBox={`0 0 ${A} ${H}`} role="img" aria-label={`${titulo} (${unidad}). ${t('gemelo.banda')}`}>
        <line className="eje" x1={IZQ} x2={IZQ} y1={ARR} y2={H - ABA} />
        <line className="eje" x1={IZQ} x2={A - DER} y1={H - ABA} y2={H - ABA} />
        <text className="marca" x={IZQ - 4} y={ARR + 8} textAnchor="end">{fmt(hi)}</text>
        <text className="marca" x={IZQ - 4} y={H - ABA} textAnchor="end">{fmt(lo)}</text>
        {Array.from({ length: anios }, (_, a) => (
          <g key={a}>
            {a > 0 && <line className="rejilla" x1={IZQ + a * ancho} x2={IZQ + a * ancho} y1={ARR} y2={H - ABA} />}
            <text className="marca" x={IZQ + (a + 0.5) * ancho} y={H - 8} textAnchor="middle">{llenar(t('lote.anio_n'), { n: String(a + 1) })}</text>
          </g>
        ))}
        {validas.map((s, k) => (
          <g key={s.id} className={`serie s${k}`}>
            <polygon className="banda" points={[...pts(s.p90), ...pts(s.p10).reverse()].join(' ')} />
            <polyline className="mediana" fill="none" points={pts(s.p50).join(' ')} />
          </g>
        ))}
      </svg>
      <ul className="leyenda">
        {validas.map((s, k) => <li key={s.id} className={`s${k}`}><span className="muestra" aria-hidden="true" /> {s.nombre}</li>)}
      </ul>
    </figure>
  )
}
