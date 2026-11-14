// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Ordenamiento del comparador (INICIAR §11.5). Corre en el cliente. No combina Efecto₂ ni β: el rendimiento solo se marca (§11.4).
export const CLAVES = ['agua', 'forraje', 'nitrogeno', 'erosion', 'materiaOrganica', 'mercado'] as const
export type Clave = (typeof CLAVES)[number]
export type Pesos = Record<Clave, number> // 0..5

// Beneficio con "más es mejor"; null = sin evidencia en la demo (no puntúa)
export type Beneficio = { v: number; rango?: [number, number] } | null

export interface Estrategia {
  id: string
  nombre: string
  cultivos: string[]
  aguaMm: number | null
  exige: { siembraDirecta: boolean; cosechaForraje: boolean } // tabla SUPUESTO
  efecto2: number | null // % frente a la habitual, tal cual de efecto_antecesor
  beneficios: Record<Clave, Beneficio>
}

export interface Restricciones {
  cultivosAceptados: string[] | null
  aguaMaxMm: number | null
  siembraDirecta: boolean
  cosechaForraje: boolean
}

export interface Ordenada {
  estrategia: Estrategia
  puntaje: number
  intervalo: [number, number]
  viola: string[]
  rindeMenosQueHabitual?: number
}

function violaciones(e: Estrategia, r: Restricciones): string[] {
  const v: string[] = []
  if (r.aguaMaxMm !== null && e.aguaMm !== null && e.aguaMm > r.aguaMaxMm) v.push(`demanda ${e.aguaMm} mm, por encima del límite de ${r.aguaMaxMm} mm`)
  if (e.exige.siembraDirecta && !r.siembraDirecta) v.push('exige siembra directa y no hay equipo (SUPUESTO)')
  if (e.exige.cosechaForraje && !r.cosechaForraje) v.push('exige cosecha de forraje y no hay equipo (SUPUESTO)')
  const fuera = r.cultivosAceptados ? e.cultivos.filter((c) => !r.cultivosAceptados!.includes(c)) : []
  if (fuera.length) v.push(`cultivos no aceptados por el mercado: ${fuera.join(', ')}`)
  return v
}

function puntuar(l: Estrategia[], p: Pesos): { puntaje: number; intervalo: [number, number] }[] {
  const suma = CLAVES.reduce((s, k) => s + p[k], 0)
  const lim = {} as Record<Clave, [number, number]>
  for (const k of CLAVES) {
    const xs = l.flatMap((e) => { const b = e.beneficios[k]; return b ? [b.v, ...(b.rango ?? [])] : [] })
    lim[k] = xs.length ? [Math.min(...xs), Math.max(...xs)] : [0, 0]
  }
  const norm = (k: Clave, x: number) => (lim[k][1] === lim[k][0] ? 0.5 : (x - lim[k][0]) / (lim[k][1] - lim[k][0]))
  return l.map((e) => {
    if (suma === 0) return { puntaje: 0, intervalo: [0, 0] }
    let a = 0, m = 0, z = 0
    for (const k of CLAVES) {
      const b = e.beneficios[k]
      if (!b || p[k] === 0) continue
      a += (p[k] * norm(k, b.rango?.[0] ?? b.v))
      m += p[k] * norm(k, b.v)
      z += p[k] * norm(k, b.rango?.[1] ?? b.v)
    }
    return { puntaje: m / suma, intervalo: [a / suma, z / suma] }
  })
}

export function ordenar(estrategias: Estrategia[], pesos: Pesos, restricciones: Restricciones): Ordenada[] {
  const pts = puntuar(estrategias, pesos)
  return estrategias
    .map((estrategia, i) => ({
      i, estrategia, ...pts[i], viola: violaciones(estrategia, restricciones),
      ...(estrategia.efecto2 !== null && estrategia.efecto2 < 0 ? { rindeMenosQueHabitual: estrategia.efecto2 } : {}),
    }))
    .sort((a, b) => b.puntaje - a.puntaje || a.i - b.i) // empate: posición original
    .map(({ i: _i, ...o }) => o)
}

export function sensibilidad(estrategias: Estrategia[], pesos: Pesos): { primeroEstable: boolean; cambioMinimoPorPeso: Record<Clave, number | null> } {
  const sr: Restricciones = { cultivosAceptados: null, aguaMaxMm: null, siembraDirecta: true, cosechaForraje: true }
  const base = ordenar(estrategias, pesos, sr)
  const primero = base[0]?.estrategia.id
  const cambio = {} as Record<Clave, number | null>
  for (const k of CLAVES) {
    cambio[k] = null
    for (let n = 1; n <= 100 && cambio[k] === null; n++) { // paso 0,05 en 0..5
      const d = n * 0.05
      for (const x of [pesos[k] + d, pesos[k] - d]) {
        if (x < 0 || x > 5) continue
        if (ordenar(estrategias, { ...pesos, [k]: x }, sr)[0]?.estrategia.id !== primero) { cambio[k] = Math.round(d * 100) / 100; break }
      }
    }
  }
  const [top, ...resto] = base
  return { primeroEstable: !!top && resto.every((o) => o.intervalo[1] < top.intervalo[0]), cambioMinimoPorPeso: cambio }
}
