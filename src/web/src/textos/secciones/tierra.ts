// asistido por SI: Claude Code (Anthropic), textos de la sección tierra (plan fase 3 v2 §10)
// Claves con prefijo 'tierra.'; el español debe tener todas las claves del inglés (lo exige el tipo)
export const en = {
  'tierra.lotes.titulo': 'Select a lot',
  'tierra.lotes.ayuda': 'DEMO plots: the camera flies to the real point and opens the plot view',
  'tierra.lotes.error': 'Could not load the DEMO plots',
  'tierra.leyenda.unidad': 'Unit',
  'tierra.leyenda.producto': 'Product',
  'tierra.suelo.noDisponible': 'Not available yet',
  'tierra.suelo.nota': 'Soil by unit is not computed yet; soil is shown only for the DEMO plots.',
} as const
export const es: Record<keyof typeof en, string> = {
  'tierra.lotes.titulo': 'Elige un lote',
  'tierra.lotes.ayuda': 'Lotes DEMO: la cámara vuela al punto real y abre la vista del lote',
  'tierra.lotes.error': 'No se pudieron cargar los lotes DEMO',
  'tierra.leyenda.unidad': 'Unidad',
  'tierra.leyenda.producto': 'Producto',
  'tierra.suelo.noDisponible': 'Aún no disponible',
  'tierra.suelo.nota': 'El suelo por unidad aún no se calcula; solo se muestra en los lotes DEMO.',
}
