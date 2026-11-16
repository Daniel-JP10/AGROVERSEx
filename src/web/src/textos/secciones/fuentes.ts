// asistido por SI: Claude Code (Anthropic), textos de la sección fuentes (plan fase 3 v2 §10)
// Claves con prefijo 'fuentes.'; el español debe tener todas las claves del inglés (lo exige el tipo)
// Créditos del equipo: nombres y áreas dados por el director (21:35)
export const en = {
  'fuentes.f.intro': 'Where every piece of data comes from, what the words mean and who made what.',
  'fuentes.f.fuentes': 'Sources and licenses',
  'fuentes.f.glosario': 'Glossary',
  'fuentes.f.creditos': 'Credits',
  'fuentes.f.credito_director': 'Director: Daniel Andres Jimenez Povea',
  'fuentes.f.credito_diseno': 'Design: Jostin Andres Colon Ramos',
  'fuentes.f.credito_gemelo': 'Digital twin: Emmanuel Ascendra Perez',
  'fuentes.f.referencias_ia': 'The visual design was drawn by hand by the team: every chart, icon and illustration on screen is our own SVG or our own rendering of our data.',
} as const
export const es: Record<keyof typeof en, string> = {
  'fuentes.f.intro': 'De dónde viene cada dato, qué significa cada palabra y quién hizo qué.',
  'fuentes.f.fuentes': 'Fuentes y licencias',
  'fuentes.f.glosario': 'Glosario',
  'fuentes.f.creditos': 'Créditos',
  'fuentes.f.credito_director': 'Director: Daniel Andres Jimenez Povea',
  'fuentes.f.credito_diseno': 'Diseño: Jostin Andres Colon Ramos',
  'fuentes.f.credito_gemelo': 'Gemelo digital: Emmanuel Ascendra Perez',
  'fuentes.f.referencias_ia': 'El diseño visual lo dibujó a mano el equipo: cada gráfico, ícono e ilustración en pantalla es un SVG nuestro o una representación nuestra de nuestros datos.',
}
