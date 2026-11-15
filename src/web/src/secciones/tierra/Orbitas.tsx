// asistido por SI: Claude Code (Anthropic), órbitas decorativas alrededor del globo; sin dato, sin satélites (plan v2 §3)
// Decoración: aria-hidden, sin eventos de puntero ni tabindex; con reduced-motion no giran (tierra.css)
export function Orbitas() {
  return (
    <svg className="orbitas" viewBox="-500 -500 1000 1000" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
      <g className="orbita orbita-a"><ellipse rx="470" ry="150" transform="rotate(-18)" /></g>
      <g className="orbita orbita-b"><ellipse rx="430" ry="230" transform="rotate(24)" /></g>
    </svg>
  )
}
