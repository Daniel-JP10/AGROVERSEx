// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { ClaveTexto } from './es'

// Si falta una clave, no compila
export const en: Record<ClaveTexto, string> = {
  'ayuda.titulo': 'Help and glossary',
  'ayuda.cerrar': 'Close help',
  'ayuda.abrir': 'Help and glossary',
  'ayuda.intro': 'AGROVERSEx (simulated mode): shows SIMULATED data imitating real satellite products. It is for ideation: these are not measurements.',
  'ayuda.glosario': 'Glossary',
  'ayuda.fuentes': 'Sources and licenses',
  'ayuda.modo': 'Reading mode',
  'modo.agricultor': 'Farmer',
  'modo.tecnico': 'Technician',
  'modo.nota': 'The mode changes how much detail the texts give, not the data.',
  'idioma.etiqueta': 'Language: English (switch to Spanish)',
  'idioma.boton': 'EN',
}
