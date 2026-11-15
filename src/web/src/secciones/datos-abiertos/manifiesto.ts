// asistido por SI: Claude Code (Anthropic), tarjetas de Datos abiertos leídas de datos/manifiesto.json (web_datos v0) en tiempo de ejecución
interface Producto { producto?: string; version?: string; unidad?: string; estado?: string }
export interface Manifiesto {
  version_contrato?: string
  generado_utc?: string
  paises?: string[]
  variables?: Record<string, { niveles?: number[]; meses_disponibles?: { desde?: string; hasta?: string; n_meses_con_producto?: number }; productos?: Producto[] }>
  archivos?: Record<string, { bytes?: number; sha256?: string }>
}

/** Una tarjeta por archivo: lo que no trae el manifiesto queda sin dato. */
export interface ArchivoAbierto {
  ruta: string
  url: string
  bytes?: number
  sha256?: string
  // Solo las series (<iso3>/<variable>_<nivel>.json.gz)
  serie?: { pais: string; variable: string; nivel: number; desde?: string; hasta?: string; meses?: number; productos: Producto[] }
  tipo: 'serie' | 'geometria' | 'proyecto'
}
export interface DatosManifiesto { generado?: string; archivos: ArchivoAbierto[] }

// Rutas relativas a public/datos/, sin subir de carpeta; huella SHA-256 en hexadecimal
const RUTA_SEGURA = /^(?!.*\.\.)[\w\-/.]+$/
const SHA = /^[0-9a-f]{64}$/
const SERIE = /^([A-Z]{3})\/(\w+?)_(\d)\.json\.gz$/
// Geometrías de unidades derivadas de geoBoundaries (ODbL por D-015); el resto es metadato del proyecto
const GEOMETRIA = /^unidades_geo\b/

export function desdeManifiesto(m: Manifiesto, base: string): DatosManifiesto {
  const archivos = Object.entries(m.archivos ?? {})
    .filter(([ruta]) => RUTA_SEGURA.test(ruta))
    .map(([ruta, a]): ArchivoAbierto => {
      const s = SERIE.exec(ruta)
      const v = s ? m.variables?.[s[2]] : undefined
      return {
        ruta,
        url: `${base}datos/${ruta}`,
        ...(typeof a.bytes === 'number' && Number.isFinite(a.bytes) ? { bytes: a.bytes } : {}),
        ...(a.sha256 && SHA.test(a.sha256) ? { sha256: a.sha256 } : {}),
        ...(s ? { serie: { pais: s[1], variable: s[2], nivel: Number(s[3]), desde: v?.meses_disponibles?.desde, hasta: v?.meses_disponibles?.hasta, meses: v?.meses_disponibles?.n_meses_con_producto, productos: v?.productos ?? [] } } : {}),
        tipo: s ? 'serie' : GEOMETRIA.test(ruta) ? 'geometria' : 'proyecto',
      }
    })
  return { generado: m.generado_utc, archivos }
}

export async function cargarManifiesto(pedir: (u: string) => Promise<Response> = (u) => fetch(u), base = import.meta.env.BASE_URL): Promise<DatosManifiesto | null> {
  try {
    const r = await pedir(`${base}datos/manifiesto.json`)
    if (!r.ok) return null
    return desdeManifiesto(await r.json() as Manifiesto, base)
  } catch {
    return null
  }
}
