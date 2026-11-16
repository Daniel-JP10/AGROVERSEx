// asistido por SI: Claude Code (Anthropic), componente que muestra un valor siempre con su rango p10 a p90
import { idioma, t } from '../../textos/i18n'

interface P { p10: number | null; p50: number | null; p90: number | null; unidad: string; entera?: boolean }

const fin = (v: number | null): v is number => typeof v === 'number' && Number.isFinite(v)
// Enteros completos (elevación, días); el resto con 3 cifras significativas
const fmt = (v: number) => new Intl.NumberFormat(idioma() === 'en' ? 'en' : 'es', Number.isInteger(v) ? { maximumFractionDigits: 0 } : { maximumSignificantDigits: 3 }).format(v)

// Un solo elemento con un solo texto: así la prueba del árbol puede aislar cada número con su banda
// entera (H-F3-9): la cifra con su rango no se parte (espacio duro y unión tras la raya); solo la unidad puede bajar de línea
export function Banda({ p10, p50, p90, unidad, entera = false }: P) {
  if (!fin(p10) || !fin(p50) || !fin(p90)) return <span data-banda="" className="banda sin-dato">{t('rotaciones.dato_no_disponible')}</span>
  const [esp, raya] = entera ? [' ', '–⁠'] : [' ', '–']
  return <span data-banda="" className="banda" title={t('rotaciones.rango')}>{`${fmt(p50)}${esp}(${fmt(p10)}${raya}${fmt(p90)}) ${unidad}`}</span>
}
