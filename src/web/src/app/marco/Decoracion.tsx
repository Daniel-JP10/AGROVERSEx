// asistido por SI: Claude Code (Anthropic), hojas decorativas de las esquinas del marco común (SVG propio)
// Decoración: aria-hidden, sin eventos de puntero y sin foco (F3_COMUN)
function Hoja({ className }: { className: string }) {
  return (
    <svg className={`hoja-esquina ${className}`} viewBox="0 0 200 200" aria-hidden="true" focusable="false">
      <path className="limbo" d="M10 190 C 20 90 90 20 190 10 C 180 110 110 180 10 190 Z" />
      <path className="nervio" d="M10 190 C 70 130 120 80 190 10" />
      <path className="nervio fino" d="M60 140 C 70 110 72 95 70 80 M100 100 C 115 90 130 85 150 85 M95 105 C 100 80 105 65 110 50 M55 145 C 80 140 100 135 125 125" />
    </svg>
  )
}

export function Decoracion() {
  return (
    <div className="decoracion" aria-hidden="true">
      <Hoja className="arriba-izquierda" />
      <Hoja className="abajo-derecha" />
    </div>
  )
}
