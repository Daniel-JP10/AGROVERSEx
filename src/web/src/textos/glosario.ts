// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { ClaveTexto } from './en'

// Cada término cita su fuente; ninguna cifra escrita a mano: la resolución y la versión de cada producto salen de los datos de Fuentes
export interface Termino { termino: string; es: string; en: string; tecnico: string; fuente: string }
export const GLOSARIO: Termino[] = [
  { termino: 'SMAP', es: 'Satélite que mide la humedad del suelo.', en: 'Satellite that measures soil moisture.', tecnico: 'Producto modelado de humedad superficial y de la zona de raíces; en el modo simulado de AGROVERSEx se imita (SIMULADO).', fuente: 'NASA SMAP' },
  { termino: 'IMERG', es: 'Estimación de lluvia combinando varios satélites.', en: 'Rainfall estimate merging several satellites.', tecnico: 'Final publica mm/hr y Late mm/day; la interfaz muestra mm/mes.', fuente: 'NASA GPM IMERG' },
  { termino: 'GRACE', es: 'Misión que detecta cambios en el agua almacenada bajo tierra.', en: 'Mission that detects changes in stored water underground.', tecnico: 'Resolución gruesa: capa de contexto regional.', fuente: 'NASA GRACE-FO' },
  { termino: 'NDVI', es: 'Índice del verdor de la vegetación.', en: 'Index of vegetation greenness.', tecnico: 'Razón normalizada rojo e infrarrojo cercano.', fuente: 'NASA MODIS' },
  { termino: 'Condición de la tierra', es: 'Clase que resume el estado de la tierra de una unidad en un periodo.', en: "Class summarizing the state of a unit's land over a period.", tecnico: 'Combinación propia de componentes; cada uno con rango y confianza.', fuente: 'Definición propia de AGROVERSEx (INFERENCIA)' },
  { termino: 'RONI', es: 'Medida de El Niño y La Niña.', en: 'Measure of El Niño and La Niña.', tecnico: 'ONI relativo; serie real mostrada bajo la línea de tiempo.', fuente: 'NOAA CPC' },
  { termino: 'SoilGrids', es: 'Mapa mundial de propiedades del suelo.', en: 'Global map of soil properties.', tecnico: 'Solo media agregada, sin intervalo, sin fecha.', fuente: 'ISRIC SoilGrids' },
  { termino: 'ADM1 / ADM2', es: 'Primer y segundo nivel administrativo (departamento y municipio).', en: 'First and second administrative level (state and county).', tecnico: 'Límites de geoBoundaries CGAZ.', fuente: 'geoBoundaries CGAZ' },
]

// Glosario de la sección Fuentes (F4, F5, F7): los textos viven en en.ts y es.ts, bloque fuentes.
// fuente es la clave del texto de la fuente y url su fuente primaria; null se muestra "source pending"
// FAO-56 y Tucker comprobados en fao.org y Crossref; SMAP L4 en CITAS.md y doi.org (2026-11-14)
const FAO56 = 'https://www.fao.org/4/x0490e/x0490e00.htm'
export interface TerminoClave { id: 'et' | 'humedad' | 'ndvi' | 'helada' | 'balance' | 'satelite' | 'incertidumbre' | 'confianza'; fuente: ClaveTexto | null; url?: string }
export const TERMINOS: readonly TerminoClave[] = [
  { id: 'et', fuente: 'glosario.et.fuente', url: FAO56 },
  { id: 'humedad', fuente: 'glosario.humedad.fuente', url: 'https://doi.org/10.5067/T5RUATAQREF8' },
  { id: 'ndvi', fuente: 'glosario.ndvi.fuente', url: 'https://doi.org/10.1016/0034-4257(79)90013-0' },
  { id: 'helada', fuente: null },
  { id: 'balance', fuente: 'glosario.balance.fuente', url: FAO56 },
  { id: 'satelite', fuente: null },
  { id: 'incertidumbre', fuente: 'glosario.incertidumbre.fuente' },
  { id: 'confianza', fuente: 'glosario.confianza.fuente' },
]
