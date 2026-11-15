// asistido por SI: Claude Code (Anthropic), componente que muestra un valor siempre con su rango p10 a p90
import { idioma, t } from '../../textos/i18n'

interface P { p10: number | null; p50: number | null; p90: number | null; unidad: string }

const fin = (v: number | null): v is number => typeof v === 'number' && Number.isFinite(v)
const fmt = (v: number) => new Intl.NumberFormat(idioma() === 'en' ? 'en' : 'es', { maximumSignificantDigits: 3 }).format(v)

// Un solo elemento con un solo texto: así la prueba del árbol puede aislar cada número con su banda
export function Banda({ p10, p50, p90, unidad }: P) {
  if (!fin(p10) || !fin(p50) || !fin(p90)) return <span data-banda="" className="banda sin-dato">{t('rotaciones.dato_no_disponible')}</span>
  return <span data-banda="" className="banda" title={t('rotaciones.rango')}>{`${fmt(p50)} (${fmt(p10)}–${fmt(p90)}) ${unidad}`}</span>
}
