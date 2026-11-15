import { t } from '../textos/i18n'
// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Fondos raster del globo. Blue Marble (local/respaldo) abajo; el fondo de detalle va encima.
export interface FondoConfig {
  id: string
  nombre: string
  tiles: string[]
  maxzoom: number
  atribucion: string
  licencia: string
  requiereToken: boolean
}

const GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best'

export const FONDOS: FondoConfig[] = [
  {
    id: 'bluemarble', nombre: 'Blue Marble (NASA GIBS)', maxzoom: 8, requiereToken: false,
    tiles: [`${GIBS}/BlueMarble_ShadedRelief_Bathymetry/default/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`],
    atribucion: 'Imágenes NASA GIBS', licencia: 'Dominio público (NASA)',
  },
  {
    // VERIFICADO 2026-11-09: capa s2cloudless-2024_3857, zoom 21 en el GetCapabilities; se limita a 14 (SUPUESTO, carga)
    id: 'eox-s2-2024', nombre: 'Sentinel-2 cloudless 2024 (EOX)', maxzoom: 14, requiereToken: false,
    tiles: ['https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg'],
    atribucion: 'EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2024)',
    licencia: 'CC BY-NC-SA 4.0',
  },
]

export const FONDO_DETALLE = 'eox-s2-2024'
export const avisoSinRed = () => t('globo.fondoSinRed')
/** Zoom en que el fondo de detalle empieza a verse y en que está a pleno. */
export const ZOOM_DETALLE: [number, number] = [3.5, 5]

export const fondoBase = () => FONDOS[0]

/** Fondo de detalle elegido, o null sin red (queda solo Blue Marble). */
export function fondoDetalle(enLinea: boolean, id: string = FONDO_DETALLE): FondoConfig | null {
  if (!enLinea) return null
  const f = FONDOS.find((x) => x.id === id)
  return f && f.id !== 'bluemarble' && !f.requiereToken ? f : null
}
