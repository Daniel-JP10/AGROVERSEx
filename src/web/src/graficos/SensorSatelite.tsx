// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useRef } from 'react'
import * as Plot from '@observablehq/plot'

type Num = number | null
// Tramos contiguos: el hueco (null) corta la línea, sin interpolar.
function tramos(dias: number[], v: Num[], serie: string) {
  let t = 0
  const out: { dia: number; v: number; serie: string; t: string }[] = []
  v.forEach((x, i) => { if (x === null) t++; else out.push({ dia: dias[i], v: x, serie, t: `${serie}${t}` }) })
  return out
}

// Sensor del agricultor frente a humedad de verdad, ambos SIMULADOS.
export function SensorSatelite({ dias, sensor, verdad }: { dias: number[]; sensor: Num[]; verdad: Num[] }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const f = Plot.plot({
      width: 288, height: 170, marginLeft: 44, color: { legend: true, domain: ['sensor', 'verdad'] },
      x: { label: 'día desde 2000-01-01' }, y: { label: 'm³/m³', grid: true },
      marks: [Plot.lineY([...tramos(dias, verdad, 'verdad'), ...tramos(dias, sensor, 'sensor')], { x: 'dia', y: 'v', z: 't', stroke: 'serie' })],
    })
    f.setAttribute('role', 'img')
    f.setAttribute('aria-label', 'Sensor frente a humedad de verdad, SIMULADO; huecos sin interpolar')
    ref.current?.replaceChildren(f)
  }, [dias, sensor, verdad])
  return <div ref={ref} data-testid="sensor-grafico" />
}
