// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Cada término cita su fuente (fichas del proyecto: INICIAR §5.2)
export interface Termino { termino: string; es: string; en: string; tecnico: string; fuente: string }
export const GLOSARIO: Termino[] = [
  { termino: 'SMAP', es: 'Satélite que mide la humedad del suelo.', en: 'Satellite that measures soil moisture.', tecnico: 'Producto L4 V008, 9 km; en el modo simulado de AGROVERSEx se imita (SIMULADO).', fuente: 'NASA SMAP L4' },
  { termino: 'IMERG', es: 'Estimación de lluvia combinando varios satélites.', en: 'Rainfall estimate merging several satellites.', tecnico: 'Publica mm/h; la interfaz convierte para mostrar.', fuente: 'NASA GPM IMERG' },
  { termino: 'GRACE', es: 'Misión que detecta cambios en el agua almacenada bajo tierra.', en: 'Mission that detects changes in stored water underground.', tecnico: 'Resolución gruesa: capa de contexto regional.', fuente: 'NASA GRACE-FO' },
  { termino: 'NDVI', es: 'Índice del verdor de la vegetación.', en: 'Index of vegetation greenness.', tecnico: 'Razón normalizada rojo e infrarrojo cercano.', fuente: 'NASA MODIS' },
  { termino: 'Condición de la tierra', es: 'Clase que resume el estado de la tierra de una unidad en un periodo.', en: "Class summarizing the state of a unit's land over a period.", tecnico: 'Combinación propia de componentes; cada uno con rango y confianza.', fuente: 'INICIAR §6' },
  { termino: 'RONI', es: 'Medida de El Niño y La Niña.', en: 'Measure of El Niño and La Niña.', tecnico: 'ONI relativo; serie real mostrada bajo la línea de tiempo.', fuente: 'NOAA CPC' },
  { termino: 'SoilGrids', es: 'Mapa mundial de propiedades del suelo.', en: 'Global map of soil properties.', tecnico: 'Solo media agregada, sin intervalo, sin fecha.', fuente: 'ISRIC SoilGrids' },
  { termino: 'ADM1 / ADM2', es: 'Primer y segundo nivel administrativo (departamento y municipio).', en: 'First and second administrative level (state and county).', tecnico: 'Límites administrativos.', fuente: 'geoBoundaries CGAZ' },
]
