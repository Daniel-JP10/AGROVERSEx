// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { AtributosUnidad } from '../../datos/filtrar'

export interface FiltroRegional { id: string; nombre: string; evidencia: string }

const TROPICO = 23.44
const z = (u: AtributosUnidad, ...claves: string[]) => !!u.zona && claves.some((c) => u.zona!.toLowerCase().includes(c))
const MACRO_SAL = ['cercano oriente', 'norte de áfrica', 'asia', 'europa', 'eurasia', 'latinoamérica']

// Condiciones de INICIAR §10.2 (SUPUESTO de diseño). Un atributo ausente nunca activa el filtro.
const REGLAS: [FiltroRegional, (u: AtributosUnidad) => boolean][] = [
  [{ id: 'piso_termico', nombre: 'Piso térmico y altitud', evidencia: 'NASADEM; error de POWER en relieve [INV-CLI §8.2]' },
    (u) => u.lat !== undefined && Math.abs(u.lat) <= TROPICO && u.elevMin !== undefined && u.elevMax !== undefined && u.elevMax - u.elevMin > 1000],
  [{ id: 'heladas', nombre: 'Calendario de heladas', evidencia: 'POWER FROST_DAYS' }, (u) => u.heladas === true],
  [{ id: 'riego', nombre: 'Riego frente a secano', evidencia: 'MIRCA2000, CC BY 4.0 [INV-ROT §7]' }, (u) => u.riego !== undefined],
  [{ id: 'agua_subterranea', nombre: 'Agua subterránea', evidencia: 'Rodell 2018 [INV-CLI §5]' }, (u) => u.grace === true],
  [{ id: 'salinidad', nombre: 'Salinidad', evidencia: 'FAO/ITPS 2015 y FAO 2024 [INV-SUE §5]' },
    (u) => !!u.macro && MACRO_SAL.includes(u.macro.toLowerCase())],
  [{ id: 'acidez', nombre: 'Acidez', evidencia: 'FAO/ITPS 2015; umbral pH < 5,5 SUPUESTO' },
    (u) => (u.ph !== undefined && u.ph < 5.5) || z(u, 'suroeste del pacífico')],
  [{ id: 'erosion_laderas', nombre: 'Erosión en laderas', evidencia: 'Borrelli 2017; pendiente > 7 % [INV-ROT §4.3]' },
    (u) => u.pendiente !== undefined && u.pendiente > 7 && u.cultivo === true],
  [{ id: 'safrinha', nombre: 'Doble cultivo, safrinha', evidencia: 'Embrapa y prensa [INV-ROT §6]' }, (u) => z(u, 'cerrado')],
  [{ id: 'kharif_rabi', nombre: 'Temporadas kharif y rabi', evidencia: '[INV-ROT §6]' }, (u) => z(u, 'indogang', 'indo_gang')],
  [{ id: 'lluvia_unica', nombre: 'Temporada de lluvias única', evidencia: 'Climatología IMERG simulada' }, (u) => u.unimodal === true && z(u, 'sahel', 'sabana')],
  [{ id: 'nematodo_papa', nombre: 'Nematodo de la papa', evidencia: 'Globodera pallida, 57 % resumen y 60 % discusión [INV-ROT §5.2]' }, (u) => z(u, 'andina_colombia')],
  [{ id: 'siembra_enso', nombre: 'Ventana de siembra ENSO', evidencia: 'MacCarthy 2017' }, (u) => z(u, 'norte_ghana', 'ghana')],
  [{ id: 'fechas_reguladas', nombre: 'Fechas reguladas de siembra', evidencia: 'Resolución ICA [INV-ROT §6]; tabla con PDF desalineado, revisar' }, (u) => z(u, 'meta', 'llanos')],
  [{ id: 'hueco_alta_latitud', nombre: 'Hueco de datos en latitudes altas', evidencia: 'NASADEM sin dato; SMAP con nieve y suelo congelado' }, (u) => u.lat !== undefined && u.lat > 60],
]

export function filtrosRegionalesPara(u: AtributosUnidad): FiltroRegional[] {
  return REGLAS.filter(([, cond]) => cond(u)).map(([f]) => f)
}
