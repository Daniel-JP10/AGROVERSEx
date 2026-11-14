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
    // VERIFICADO 2026-11-14 en GetCapabilities: MODIS Terra TrueColor, GoogleMapsCompatible_Level9, jpeg; fecha fija (SUPUESTO: sin nubes aceptables)
    id: 'gibs-modis-terra', nombre: 'MODIS Terra color verdadero (NASA GIBS)', maxzoom: 9, requiereToken: false,
    tiles: [`${GIBS}/MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-08-01/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`],
    atribucion: "We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS).",
    licencia: 'Datos abiertos de NASA (uso libre con reconocimiento)',
  },
]

export const FONDO_DETALLE = 'gibs-modis-terra'
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
