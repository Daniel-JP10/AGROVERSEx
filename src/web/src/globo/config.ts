// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { fondoBase, fondoDetalle, ZOOM_DETALLE } from './fondos'
import { t } from '../textos/i18n'
// Configuración centralizada de capas del globo.
// Teselas reales de GADM (adm0/adm1/adm2), generadas en la fase 1. Propiedades: id (texto),
// nivel, iso3, padre_id, nombre, es_disputa. Las zonas en disputa (es_disputa = 1) están en las tres capas.

export interface NivelConfig {
  /** Posición en la jerarquía: 0 = país, 1 = departamento, 2 = municipio */
  nivel: number
  /** Nombre de la fuente MapLibre y de la capa dentro del PMTiles */
  fuente: string
  /** Ruta del PMTiles, relativa al origen del sitio */
  archivo: string
  /** Nombre de la capa vectorial dentro del archivo */
  capaFuente: string
  /** Propiedad con el id estable (texto en GADM) */
  propId: string
  /** Rango de zoom de las teselas (informativo y para la transición) */
  zoomDesde: number
  zoomHasta: number
  /** Ancho de la entrada cruzada de este nivel, en zoom; a partir de desde+fundido es interactivo */
  fundido: number
  /** Países sin nivel inferior: este nivel sigue visible como respaldo en su lugar */
  sinHijo: readonly string[]
}

// Países con ADM1 pero sin ADM2 en GADM (derivado de `unidad` en geo.sqlite; GHA sí tiene ADM2, con ids atípicos como GHA1.1_2)
export const SIN_ADM2: readonly string[] = ['ABW', 'AIA', 'AND', 'ATA', 'ATF', 'ATG', 'BES', 'BHR', 'BMU', 'BRB', 'BVT', 'CCK', 'COK', 'CUW', 'CXR', 'CYM', 'DMA', 'ESH', 'FLK', 'GGY', 'GIB', 'GRD', 'GRL', 'HMD', 'IMN', 'IOT', 'JEY', 'KNA', 'LBY', 'LIE', 'MAF', 'MDA', 'MHL', 'MNE', 'MSR', 'MUS', 'MYT', 'NFK', 'NIU', 'NRU', 'PCN', 'PYF', 'SGS', 'SJM', 'SMR', 'SPM', 'SXM', 'TCA', 'TKL', 'TTO', 'UMI', 'VAT', 'VCT', 'VGB', 'XAD', 'XCA', 'XCL', 'XPI', 'XSP', 'ZNC']
// Países que solo existen como ADM0
export const SIN_ADM1: readonly string[] = ['ABW', 'ATA', 'BVT', 'CCK', 'CUW', 'CXR', 'FLK', 'GIB', 'HMD', 'IOT', 'KIR', 'MAF', 'MCO', 'MDV', 'NFK', 'NIU', 'PCN', 'SGS', 'SXM', 'VAT', 'XCA', 'XCL', 'XPI', 'XSP']

export const NIVELES: NivelConfig[] = [
  { nivel: 0, fuente: 'adm0', archivo: '/teselas/adm0.pmtiles', capaFuente: 'adm0', propId: 'id', zoomDesde: 0, zoomHasta: 6, fundido: 0, sinHijo: SIN_ADM1 },
  { nivel: 1, fuente: 'adm1', archivo: '/teselas/adm1.pmtiles', capaFuente: 'adm1', propId: 'id', zoomDesde: 2, zoomHasta: 9, fundido: 0.5, sinHijo: SIN_ADM2 },
  { nivel: 2, fuente: 'adm2', archivo: '/teselas/adm2.pmtiles', capaFuente: 'adm2', propId: 'id', zoomDesde: 6, zoomHasta: 12, fundido: 1, sinHijo: [] },
]

/** Zona en disputa: es_disputa = 1 en adm0, adm1 y adm2 (nivel normal, iso3 111..129 o ESH). */
// Las teselas aún no llevan es_disputa (contratos/unidades.md): se deriva de iso3 (111..129 o ESH) hasta que D-016 lo agregue
export const ISO3_DISPUTA = [...Array.from({ length: 19 }, (_, i) => String(111 + i)), 'ESH']
export const esDisputa = (p?: { es_disputa?: unknown; iso3?: unknown } | null) =>
  Number(p?.es_disputa) === 1 || ISO3_DISPUTA.includes(String(p?.iso3))
const exprDisputa = ['any', ['==', ['get', 'es_disputa'], 1], ['in', ['get', 'iso3'], ['literal', ISO3_DISPUTA]]]
/** Nombre que ve el usuario: una zona en disputa nunca sale como país ni con su código. */
export const nombreUnidad = (nombre: string, disputa: boolean) => (disputa ? t('unidad.disputa') : nombre)
export const avisoDisputa = () => t('globo.disputa')

export const INDICE_BUSQUEDA = '/teselas/indice_busqueda.json.gz'

/** Nivel con el que se interactúa a un zoom dado (el más profundo ya entrado a pleno). */
export function nivelParaZoom(zoom: number): number {
  let n = 0
  for (const c of NIVELES) if (zoom >= c.zoomDesde + c.fundido) n = c.nivel
  return n
}

export const NOMBRE_NIVEL = ['País', 'Departamento', 'Municipio'] as const

// Fondo: NASA GIBS WMTS, EPSG:3857, dominio público.
const GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best'
export const FONDO_BLUEMARBLE = { tiles: fondoBase().tiles, maxzoom: fondoBase().maxzoom }
/** True Color por fecha (YYYY-MM-DD). Capa opcional, desactivada por defecto. */
export function urlTrueColor(fecha: string): string {
  return `${GIBS}/MODIS_Terra_CorrectedReflectance_TrueColor/default/${fecha}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`
}
export const TRUECOLOR_ACTIVO = false
export const FECHA_TRUECOLOR = '2024-06-15'

export const ATRIBUCION = `Imágenes NASA GIBS · ${fondoDetalle(true)!.atribucion} · Límites GADM 4.1 (uso no comercial)`

/** Capas con las que se interactúa en un nivel: su relleno y los respaldos de los niveles superiores. */
export function capasInteractivas(nivel: number): string[] {
  return NIVELES.filter((c) => c.nivel <= nivel).flatMap((c) =>
    [...(c.nivel === nivel ? [`${c.fuente}-relleno`, `${c.fuente}-disputa`] : []), ...(c.sinHijo.length ? [`${c.fuente}-respaldo`] : [])])
}

// Paleta de la coropleta de prueba (tierra seca -> agua), valores 0..1.
export const PALETA: [number, string][] = [
  [0, '#8a4a28'],
  [0.35, '#c99a4a'],
  [0.6, '#9bb26a'],
  [1, '#2b8f93'],
]

export const ESTADO_VALOR = 'v'
export const OPACIDAD = 62 // % por defecto de la coropleta
const COLOR_VALOR = ['interpolate', ['linear'], ['coalesce', ['feature-state', ESTADO_VALOR], 0.5], ...PALETA.flat()]

const estadoBool = (clave: string) => ['boolean', ['feature-state', clave], false]

// Factor de opacidad por zoom: 1 con el relleno a pleno; entra con fundido y sale al entrar el nivel siguiente
function paradas(c: NivelConfig): [number, number][] {
  const sig = NIVELES[c.nivel + 1]
  const alEntrar: [number, number][] = c.zoomDesde === 0 ? [[0, 1]] : [[c.zoomDesde, 0], [c.zoomDesde + c.fundido, 1]]
  // El nivel saliente sigue a pleno hasta que el siguiente ya tiene color (D-015: ADM2 se pinta desde z7)
  const salida: [number, number][] = sig ? [[sig.zoomDesde + sig.fundido - 0.02, 1], [sig.zoomDesde + sig.fundido, 0]] : []
  return [...alEntrar, ...salida]
}
// Cada parada vale k*tope solo si la unidad cumple la condición (ok pinta color, hueco pinta trama)
const stops = (c: NivelConfig, clave: string, tope: number) =>
  ['interpolate', ['linear'], ['zoom'], ...paradas(c).flatMap(([z, k]) => [z, ['case', estadoBool(clave), k * tope, 0]])] as unknown[]

/** Opacidad del relleno de color de un nivel (op en 0..100). respaldo: sin zoom, siempre visible. */
export function opacidadRelleno(c: NivelConfig, op: number, respaldo = false): unknown {
  return respaldo ? ['case', estadoBool('ok'), op / 100, 0] : stops(c, 'ok', op / 100)
}

/** Capas de cada nivel: relleno (coropleta), huecos, contorno, hover y selección. */
export function capasNivel(c: NivelConfig) {
  const sig = NIVELES[c.nivel + 1]
  const base = { source: c.fuente, 'source-layer': c.capaFuente }
  // +1: MapLibre filtra capas por el zoom entero de la tesela; a z6,5-7 ya usa teselas 7 y un tope en 7 las descartaría. La opacidad ya es 0 pasado el relevo
  const rango = { ...base, minzoom: c.zoomDesde, maxzoom: sig ? sig.zoomDesde + sig.fundido + 1 : 24 }
  const rl = { ...base, minzoom: c.zoomDesde, maxzoom: 24 } // los contornos no desaparecen al acercar
  const en = estadoBool
  const sinDisputa = ['!', exprDisputa]
  const enRespaldo = ['in', ['get', 'iso3'], ['literal', c.sinHijo]]
  const relFiltro = c.sinHijo.length ? ['all', sinDisputa, ['!', enRespaldo]] : sinDisputa
  const relleno = (id: string, filter: unknown, ext: object, respaldo: boolean) => ({
    id, type: 'fill', ...ext, filter, paint: { 'fill-color': COLOR_VALOR, 'fill-opacity': opacidadRelleno(c, OPACIDAD, respaldo) },
  })
  // Trama de huecos: misma geometría que el relleno; solo se ve donde el estado es hueco (sin dato del producto)
  const huecos = (id: string, filter: unknown, ext: object, respaldo: boolean) => ({
    id, type: 'fill', ...ext, filter,
    paint: { 'fill-pattern': 'sin-dato', 'fill-opacity': respaldo ? ['case', estadoBool('hueco'), 0.85, 0] : stops(c, 'hueco', 0.85) },
  })
  return [
    // Los países sin nivel inferior salen por la capa de respaldo, que no se funde al acercar
    relleno(`${c.fuente}-relleno`, relFiltro, rango, false),
    huecos(`${c.fuente}-huecos`, relFiltro, rango, false),
    ...(c.sinHijo.length ? [
      relleno(`${c.fuente}-respaldo`, ['all', sinDisputa, enRespaldo], rl, true),
      huecos(`${c.fuente}-huecos-respaldo`, ['all', sinDisputa, enRespaldo], rl, true),
    ] : []),
    {
      id: `${c.fuente}-disputa`, type: 'fill', ...rango, filter: exprDisputa,
      paint: { 'fill-pattern': 'trama', 'fill-opacity': 0.8 },
    },
    {
      id: `${c.fuente}-linea`, type: 'line', ...rl,
      // Al acercar el contorno se aclara y engrosa: sobre el satélite el color casi no se percibe
      paint: {
        'line-color': ['interpolate', ['linear'], ['zoom'], 6, '#0b0e12', 9, '#eef2f7'],
        'line-opacity': ['interpolate', ['linear'], ['zoom'], 0, 0.55, 9, 0.95],
        'line-width': ['interpolate', ['linear'], ['zoom'], 0, c.nivel === 0 ? 0.8 : 0.5, 9, 1.4, 12, 2.4],
      },
    },
    {
      id: `${c.fuente}-hover`, type: 'line', ...rl,
      paint: { 'line-color': '#ffffff', 'line-width': 2, 'line-opacity': ['case', en('hover'), 1, 0] },
    },
    {
      id: `${c.fuente}-sel`, type: 'line', ...rl,
      paint: { 'line-color': '#ffb84d', 'line-width': 3, 'line-opacity': ['case', en('sel'), 1, 0] },
    },
  ]
}

export function construirEstilo(origen: string, enLinea = true): unknown {
  const det = fondoDetalle(enLinea)
  const fuentes: Record<string, unknown> = {
    bluemarble: { type: 'raster', tileSize: 256, ...FONDO_BLUEMARBLE },
    ...(det ? { detalle: { type: 'raster', tileSize: 256, tiles: det.tiles, maxzoom: det.maxzoom } } : {}),
    truecolor: { type: 'raster', tileSize: 256, tiles: [urlTrueColor(FECHA_TRUECOLOR)], maxzoom: 9 },
  }
  for (const c of NIVELES) fuentes[c.fuente] = { type: 'vector', url: `pmtiles://${origen}${c.archivo}`, promoteId: c.propId }
  return {
    version: 8,
    projection: { type: 'globe' },
    // Atmósfera azul en el borde; se apaga al acercarse
    sky: {
      'sky-color': '#2a7fe8', 'horizon-color': '#8fd0ff', 'fog-color': '#2b2a7a',
      'sky-horizon-blend': 0.7, 'horizon-fog-blend': 0.6, 'fog-ground-blend': 0.3,
      'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 5, 1, 7, 0],
    },
    sources: fuentes,
    layers: [
      { id: 'bluemarble', type: 'raster', source: 'bluemarble' },
      ...(det ? [{ id: 'detalle', type: 'raster', source: 'detalle', paint: { 'raster-opacity': ['interpolate', ['linear'], ['zoom'], ZOOM_DETALLE[0], 0, ZOOM_DETALLE[1], 1], 'raster-fade-duration': 300 } }] : []),
      { id: 'truecolor', type: 'raster', source: 'truecolor', layout: { visibility: TRUECOLOR_ACTIVO ? 'visible' : 'none' } },
      ...NIVELES.flatMap(capasNivel),
    ],
  }
}
