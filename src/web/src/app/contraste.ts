// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Contraste WCAG 2.x entre dos colores #rrggbb
const lin = (c: number) => (c /= 255) <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
function luz(hex: string) {
  const [r, g, b] = [1, 3, 5].map((i) => lin(parseInt(hex.slice(i, i + 2), 16)))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
export function contraste(a: string, b: string) {
  const [x, y] = [luz(a), luz(b)].sort((p, q) => q - p)
  return (x + 0.05) / (y + 0.05)
}
