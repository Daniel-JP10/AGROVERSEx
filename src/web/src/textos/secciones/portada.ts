// asistido por SI: Claude Code (Anthropic), textos de la sección portada (plan fase 3 v2 §10)
// Claves con prefijo 'portada.'; el español debe tener todas las claves del inglés (lo exige el tipo)
// Frase del universo: texto del director (punto 7, 13:15)
export const en = {
  'portada.universo': 'Your land through NASA open data, from space down to your field.',
  'portada.universo_2': 'Compare rotations with a digital twin that shows ranges, not promises.',
  'portada.comenzar': 'Start',
  'portada.nodos': 'Explore by section',
  'portada.nodo.tierra': 'Earth from space',
  'portada.nodo.lote': "Your field's twin",
  'portada.nodo.rotaciones': 'Rotations',
  'portada.nodo.ciencia': 'Science and validation',
  'portada.nodo.datos': 'Open data',
  'portada.nodo.fuentes': 'Sources, glossary and credits',
} as const
export const es: Record<keyof typeof en, string> = {
  'portada.universo': 'Tu tierra vista con datos abiertos de la NASA, del espacio a tu lote.',
  'portada.universo_2': 'Compara rotaciones con un gemelo digital que muestra rangos, no promesas.',
  'portada.comenzar': 'Comenzar',
  'portada.nodos': 'Explora por sección',
  'portada.nodo.tierra': 'La Tierra desde el espacio',
  'portada.nodo.lote': 'El gemelo de tu lote',
  'portada.nodo.rotaciones': 'Rotaciones',
  'portada.nodo.ciencia': 'Ciencia y validación',
  'portada.nodo.datos': 'Datos abiertos',
  'portada.nodo.fuentes': 'Fuentes, glosario y créditos',
}
