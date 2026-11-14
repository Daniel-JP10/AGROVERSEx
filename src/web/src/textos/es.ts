// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Textos en español; las claves definen ClaveTexto
export const es = {
  'ayuda.titulo': 'Ayuda y glosario',
  'ayuda.cerrar': 'Cerrar ayuda',
  'ayuda.abrir': 'Ayuda y glosario',
  'ayuda.intro': 'AGROVERSEx (modo simulado): muestra datos SIMULADOS que imitan productos satelitales reales. Sirve para ideación: no son mediciones.',
  'ayuda.glosario': 'Glosario',
  'ayuda.fuentes': 'Fuentes y licencias',
  'ayuda.modo': 'Modo de lectura',
  'modo.agricultor': 'Agricultor',
  'modo.tecnico': 'Técnico',
  'modo.nota': 'El modo cambia el detalle de los textos, no los datos.',
  'idioma.etiqueta': 'Idioma: español (cambiar a inglés)',
  'idioma.boton': 'ES',
} as const
export type ClaveTexto = keyof typeof es
