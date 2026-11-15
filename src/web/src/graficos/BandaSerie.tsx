// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useRef } from 'react'
import * as Plot from '@observablehq/plot'
import type { Num } from '../datos/series'

export interface CambioFuente { mes: number; texto: string }
interface P { valor: Num[]; p10?: Num[]; p90?: Num[]; variable: string; unidad: string; cambiosFuente: CambioFuente[]; desde?: number }

const anio = (m: number) => 2000 + m / 12

// Tramos contiguos con dato (z distinto por tramo): el hueco corta la línea y la banda, sin interpolar.
function tramos(valor: Num[], p10: Num[] | undefined, p90: Num[] | undefined, desde: number, banda: boolean) {
  let t = 0
  const out: { mes: number; v: number; lo: number; hi: number; t: number }[] = []
  valor.forEach((v, i) => {
    const lo = p10?.[i] ?? null, hi = p90?.[i] ?? null
    if (v === null || (banda && (lo === null || hi === null))) { t++; return }
    out.push({ mes: desde + i, v, lo: lo ?? v, hi: hi ?? v, t })
  })
  return out
}

// Banda p10-p90 (areaY y1/y2) y línea; cada cambio de fuente es una regla vertical rotulada.
export function BandaSerie({ valor, p10, p90, variable, unidad, cambiosFuente, desde = 0 }: P) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const f = Plot.plot({
      width: 288, height: 170, marginLeft: 44, marginTop: 16,
      x: { label: null, tickFormat: (d: number) => String(Math.round(d)) }, y: { label: unidad, grid: true },
      marks: [
        ...(p10 && p90 ? [Plot.areaY(tramos(valor, p10, p90, desde, true), { x: (d) => anio(d.mes), y1: 'lo', y2: 'hi', z: 't', fillOpacity: 0.25 })] : []),
        Plot.lineY(tramos(valor, undefined, undefined, desde, false), { x: (d) => anio(d.mes), y: 'v', z: 't' }),
        Plot.ruleX(cambiosFuente, { x: (c: CambioFuente) => anio(c.mes), strokeDasharray: '3 3' }),
        Plot.text(cambiosFuente, { x: (c: CambioFuente) => anio(c.mes), text: 'texto', frameAnchor: 'top', dy: -12, fontSize: 9 }),
      ],
    })
    f.setAttribute('role', 'img')
    f.setAttribute('aria-label', `Serie mensual de ${variable}`)
    f.setAttribute('aria-description', `${valor.filter((x) => x !== null).length} de ${valor.length} meses con dato; huecos sin interpolar; ${cambiosFuente.map((c) => c.texto).join(', ')}`)
    ref.current?.replaceChildren(f)
  }, [valor, p10, p90, variable, unidad, cambiosFuente, desde])
  return <div ref={ref} data-testid="grafico" />
}
