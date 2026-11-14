// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { RespRotaciones } from './datos'

// Fixtures con la forma de las tablas reales; cifras de ejemplo de INICIAR §11, no del dataset
const cultivos = [
  { id: 'maiz', nombre: 'Maíz', familia: 'Poaceae', fija_n: 0, ndfa_media: null, etiqueta: 'FUENTE' },
  { id: 'soya', nombre: 'Soya', familia: 'Fabaceae', fija_n: 1, ndfa_media: 0.6, etiqueta: 'FUENTE' },
  { id: 'trebol', nombre: 'trébol rojo', familia: 'Fabaceae', fija_n: 1, ndfa_media: 0.7, etiqueta: 'FUENTE' },
  { id: 'alfalfa', nombre: 'alfalfa', familia: 'Fabaceae', fija_n: 1, ndfa_media: 0.8, etiqueta: 'FUENTE' },
]
export const FIX_CORN_BELT: RespRotaciones = {
  vacio: false,
  sistemas: [{ id: 'cornbelt', region: 'Corn Belt', habitual: 'Maíz y soya', alternativa_1: 'Maíz, soya y cereal menor con trébol rojo', alternativa_2: 'Maíz, soya, cereal y alfalfa', fuente_id: 'Marsden2003', etiqueta: 'FUENTE' }],
  antecesor: [
    { pais: 'Estados Unidos', antecesor: 'trébol rojo', cultivo: 'maíz', efecto2: 4.5, eff_div: 3.1, beta_lluvia: -1.2, beta_t: 0.8, significativo: 1, fuente_id: 'Kluger2025' },
    { pais: 'Estados Unidos', antecesor: 'alfalfa', cultivo: 'maíz', efecto2: -5.5, eff_div: -4.0, beta_lluvia: 0.5, beta_t: -0.7, significativo: 0, fuente_id: 'Kluger2025' },
  ],
  cultivos, sucesion: [{ cultivo_o_familia: 'soya', enfermedad: 'nematodo', intervalo_min: 2, intervalo_max: 2, clima: 'templado', fuente_id: 'INV-ROT5' }],
}
export const FIX_PAMPA: RespRotaciones = {
  vacio: false,
  sistemas: [{ id: 'pampa', region: 'Pampa', habitual: 'Trigo y soya de segunda, maíz, soya', alternativa_1: 'PENDIENTE', alternativa_2: 'PENDIENTE', fuente_id: 'INV-ROT6', etiqueta: 'PENDIENTE' }],
  antecesor: [], cultivos, sucesion: [],
}
export const FIX_CHINA: RespRotaciones = {
  vacio: false,
  sistemas: [{ id: 'ncp', region: 'North China Plain', habitual: 'Trigo y maíz', alternativa_1: 'Maní, luego trigo y maíz', alternativa_2: 'Batata, algodón, batata, trigo y maíz', fuente_id: 'INV-ROT6', etiqueta: 'FUENTE' }],
  antecesor: [], cultivos, sucesion: [],
}
export const FIX_VACIO: RespRotaciones = { vacio: true, motivo: 'sin sistema de rotación documentado', regiones_disponibles: ['Corn Belt', 'Pampa'] }
