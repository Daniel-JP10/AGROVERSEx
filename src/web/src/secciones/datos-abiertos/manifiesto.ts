// asistido por SI: Claude Code (Anthropic), ficha de Datos abiertos leída de datos/manifiesto.json según contratos/web_datos.md v0
import type { FichaDatos } from './DatosAbiertos'

interface Producto { producto?: string; version?: string; estado?: string }
export interface Manifiesto {
  version_contrato?: string
  generado_utc?: string
  paises?: string[]
  variables?: Record<string, { meses_disponibles?: { desde?: string; hasta?: string }; productos?: Producto[] }>
  archivos?: Record<string, { bytes?: number; sha256?: string }>
}

// Rutas del manifiesto, relativas a public/datos/; sin subir de carpeta
const RUTA_SEGURA = /^(?!.*\.\.)[\w\-/.]+$/
const SHA = /^[0-9a-f]{64}$/

/** Solo lo que trae el manifiesto; licencia, atribuciones, cita y comando no están en web_datos v0 y quedan sin dato. */
export function fichaDesdeManifiesto(m: Manifiesto, base: string): FichaDatos {
  const vars = Object.entries(m.variables ?? {})
  const desdes = vars.map(([, v]) => v.meses_disponibles?.desde).filter((x): x is string => !!x).sort()
  const hastas = vars.map(([, v]) => v.meses_disponibles?.hasta).filter((x): x is string => !!x).sort()
  const campos: FichaDatos['campos'] = {}
  if (m.version_contrato) campos.contenido = m.version_contrato
  if (desdes.length && hastas.length) campos.periodo = `${desdes[0]} – ${hastas[hastas.length - 1]}`
  if (vars.length) campos.variables = vars.map(([id, v]) => `${id}: ${(v.productos ?? []).map((p) => [p.producto, p.version, p.estado].filter(Boolean).join(' · ')).join('; ')}`).join(' | ')
  if (m.paises?.length) campos.cobertura = m.paises.join(', ')
  const descargas = Object.entries(m.archivos ?? {})
    .filter(([ruta]) => RUTA_SEGURA.test(ruta))
    .map(([ruta, a]) => ({ nombre: ruta, url: `${base}datos/${ruta}`, ...(a.sha256 && SHA.test(a.sha256) ? { sha256: a.sha256 } : {}) }))
  return { campos, descargas }
}

export async function cargarManifiesto(pedir: (u: string) => Promise<Response> = (u) => fetch(u), base = import.meta.env.BASE_URL): Promise<FichaDatos> {
  try {
    const r = await pedir(`${base}datos/manifiesto.json`)
    if (!r.ok) return {}
    return fichaDesdeManifiesto(await r.json() as Manifiesto, base)
  } catch {
    return {}
  }
}
