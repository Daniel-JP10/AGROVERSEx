// asistido por SI: Claude Code (Anthropic), frente de Pareto de dos objetivos con selector de ejes y línea base marcada
import { useEffect, useRef, useState } from 'react'
import * as Plot from '@observablehq/plot'
import { idioma, t } from '../../textos/i18n'
import { nombreEstrategia } from '../lote/datos'
import { aIngles } from './correccionEn'
import { Banda } from './Banda'
import type { EstrategiaGemelo, Objetivo } from './gemelo'

interface Punto { id: string; nombre: string; base: boolean; x: number; x10: number; x90: number; y: number; y10: number; y90: number }

const fin = (v: number | null): v is number => typeof v === 'number' && Number.isFinite(v)
const sentido = (o: Objetivo) => t(o.sentido === 'max' ? 'rotaciones.mayor_mejor' : 'rotaciones.menor_mejor')
// Unidades y nombres de los paquetes vienen en español: en inglés pasan por aIngles y nombreEstrategia
const uni = (u: string) => (idioma() === 'en' ? aIngles(u) : u)
const nombre = (e: EstrategiaGemelo) => (idioma() === 'en' ? nombreEstrategia(e) : e.nombre)
const rotulo = (o: Objetivo, e: EstrategiaGemelo) => `${o.texto} (${uni(e.indicadores[o.indicador]?.unidad ?? '')}), ${sentido(o)}`

// Solo entran los puntos con p10, p50 y p90 en los dos ejes; los demás quedan fuera sin rellenar
function puntos(es: EstrategiaGemelo[], base: string, ox: Objetivo, oy: Objetivo): Punto[] {
  const out: Punto[] = []
  for (const e of es) {
    const a = e.indicadores[ox.indicador], b = e.indicadores[oy.indicador]
    if (!a || !b || ![a.p10, a.p50, a.p90, b.p10, b.p50, b.p90].every(fin)) continue
    out.push({ id: e.id, nombre: nombre(e), base: e.id === base, x: a.p50!, x10: a.p10!, x90: a.p90!, y: b.p50!, y10: b.p10!, y90: b.p90! })
  }
  return out
}

export function FrentePareto({ objetivos, linea_base, frente }: { objetivos: Objetivo[]; linea_base: EstrategiaGemelo; frente: EstrategiaGemelo[] }) {
  const [ix, setIx] = useState(0)
  const [iy, setIy] = useState(Math.min(1, objetivos.length - 1))
  const ref = useRef<HTMLDivElement>(null)
  const todas = [linea_base, ...frente]
  const ox = objetivos[ix], oy = objetivos[iy]
  useEffect(() => {
    if (!ox || !oy || !ref.current) return
    const p = puntos(todas, linea_base.id, ox, oy)
    const alt = p.filter((d) => d.base), cand = p.filter((d) => !d.base)
    // Colores del tema oscuro (tema.css): texto claro, agua para el frente y acento para la línea base
    ref.current.replaceChildren(Plot.plot({
      width: 640, height: 380, marginLeft: 56, marginBottom: 56, style: { background: 'transparent', color: '#e9ede8', fontSize: '12px' },
      x: { label: rotulo(ox, linea_base), grid: true }, y: { label: rotulo(oy, linea_base), grid: true },
      marks: [
        Plot.ruleY(p, { y: 'y', x1: 'x10', x2: 'x90', stroke: '#a4b1ab' }),
        Plot.ruleX(p, { x: 'x', y1: 'y10', y2: 'y90', stroke: '#a4b1ab' }),
        Plot.dot(cand, { x: 'x', y: 'y', r: 5, fill: '#5cc8cc' }),
        Plot.text(cand, { x: 'x', y: 'y', text: 'id', dy: -10, fill: '#e9ede8' }),
        Plot.dot(alt, { x: 'x', y: 'y', r: 8, symbol: 'diamond', fill: '#ffb84d', stroke: '#e9ede8' }),
        Plot.text(alt, { x: 'x', y: 'y', text: () => t('rotaciones.linea_base'), dy: -14, fill: '#ffb84d' }),
      ],
    }))
  })
  if (!ox || !oy) return <p className="sin-dato">{t('aviso.sin_dato')}</p>
  const selector = (etiqueta: 'rotaciones.eje_x' | 'rotaciones.eje_y', valor: number, cambia: (n: number) => void) => (
    <label>{t(etiqueta)}
      <select value={valor} onChange={(e) => cambia(Number(e.target.value))}>
        {objetivos.map((o, i) => <option key={o.id} value={i}>{o.texto}</option>)}
      </select>
    </label>
  )
  return (
    <section className="pareto" aria-labelledby="h-pareto">
      <h2 id="h-pareto">{t('rotaciones.pareto_titulo')}</h2>
      <div className="ejes">{selector('rotaciones.eje_x', ix, setIx)}{selector('rotaciones.eje_y', iy, setIy)}</div>
      <div ref={ref} role="img" aria-label={t('rotaciones.pareto_alt')} data-testid="pareto" className="pareto-grafico" />
      <details data-testid="pareto-alternativa">
        <summary>{t('rotaciones.datos_grafico')}</summary>
        <table>
          <thead><tr><th scope="col" /><th scope="col">{ox.texto}</th><th scope="col">{oy.texto}</th></tr></thead>
          <tbody>
            {todas.map((e) => {
              const a = e.indicadores[ox.indicador], b = e.indicadores[oy.indicador]
              const base = e.id === linea_base.id
              return (
                <tr key={e.id} data-testid={base ? 'pareto-linea-base' : undefined}>
                  <th scope="row">{base ? `${nombre(e)} (${t('rotaciones.linea_base')})` : `${nombre(e)} (${e.id})`}</th>
                  <td>{a ? <Banda p10={a.p10} p50={a.p50} p90={a.p90} unidad={uni(a.unidad)} /> : <Banda p10={null} p50={null} p90={null} unidad="" />}</td>
                  <td>{b ? <Banda p10={b.p10} p50={b.p50} p90={b.p90} unidad={uni(b.unidad)} /> : <Banda p10={null} p50={null} p90={null} unidad="" />}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </details>
    </section>
  )
}
