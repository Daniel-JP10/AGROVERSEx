// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { Icono } from '../../app/iconos'
import { t } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/es'

export const HERRAMIENTAS: { id: string; clave: ClaveTexto; atajo?: string }[] = [
  { id: 'capas', clave: 'capas.titulo' },
  { id: 'filtros', clave: 'filtros.titulo' },
  { id: 'medir', clave: 'medir.titulo' },
  { id: 'comparar', clave: 'riel.comparar' },
  { id: 'escenario', clave: 'escenario.titulo' },
  { id: 'fuentes', clave: 'capas.fuentes' },
]

export function Riel({ activa, onElegir }: { activa: string; onElegir: (id: string) => void }) {
  return (
    <nav className="riel" aria-label={t('riel.titulo')}>
      {HERRAMIENTAS.map((h) => { const etiqueta = t(h.clave); return (
        <button key={h.id} type="button" aria-label={etiqueta} aria-pressed={activa === h.id}
          title={h.atajo ? `${etiqueta} (${h.atajo})` : etiqueta} onClick={() => onElegir(h.id)}>
          <Icono id={h.id} />
          <span className="etq" aria-hidden="true">{etiqueta}</span>
        </button>
      ) })}
    </nav>
  )
}
