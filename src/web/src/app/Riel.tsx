// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { Icono } from './iconos'

export const HERRAMIENTAS: { id: string; etiqueta: string; atajo?: string }[] = [
  { id: 'capas', etiqueta: 'Capas' },
  { id: 'filtros', etiqueta: 'Filtros' },
  { id: 'medir', etiqueta: 'Medir' },
  { id: 'comparar', etiqueta: 'Comparar' },
  { id: 'escenario', etiqueta: 'Escenario' },
  { id: 'fuentes', etiqueta: 'Fuentes' },
]

export function Riel({ activa, onElegir }: { activa: string; onElegir: (id: string) => void }) {
  return (
    <nav className="riel" aria-label="Herramientas">
      {HERRAMIENTAS.map((h) => (
        <button key={h.id} type="button" aria-label={h.etiqueta} aria-pressed={activa === h.id}
          title={h.atajo ? `${h.etiqueta} (${h.atajo})` : h.etiqueta} onClick={() => onElegir(h.id)}>
          <Icono id={h.id} />
          <span className="etq" aria-hidden="true">{h.etiqueta}</span>
        </button>
      ))}
    </nav>
  )
}
