// asistido por SI: Claude Code (Anthropic), íconos SVG propios de los nodos de la entrada (sin recursos de terceros)
// Todos van dentro de un enlace con texto visible: el ícono es decoración (aria-hidden)
const P = { viewBox: '0 0 64 64', 'aria-hidden': true, focusable: false, className: 'icono-nodo' } as const

export const IconoGlobo = () => (
  <svg {...P}><circle cx="32" cy="32" r="22" /><path d="M10 32 H54 M32 10 C 22 20 22 44 32 54 M32 10 C 42 20 42 44 32 54 M14 21 C 24 25 40 25 50 21 M14 43 C 24 39 40 39 50 43" /></svg>
)
export const IconoLote = () => (
  <svg {...P}><path d="M8 26 L32 14 L56 26 L32 38 Z" /><path d="M8 26 V38 L32 50 L56 38 V26 M32 38 V50" /><path d="M16 26 L36 16 M24 30 L44 20 M30 34 L50 24" /></svg>
)
export const IconoRotaciones = () => (
  <svg {...P}><path d="M32 12 A20 20 0 0 1 52 32" /><path d="M47 29 L52 34 L56 28" /><path d="M52 32 A20 20 0 0 1 32 52" /><path d="M35 47 L30 52 L36 56" /><path d="M32 52 A20 20 0 0 1 12 32 A20 20 0 0 1 32 12" /><path d="M32 24 C 26 30 26 38 32 42 C 38 38 38 30 32 24 Z M32 42 V48" /></svg>
)
export const IconoCiencia = () => (
  <svg {...P}><circle cx="27" cy="27" r="14" /><path d="M37 37 L52 52" /><path d="M20 30 C 24 24 28 32 34 24" /></svg>
)
export const IconoDatos = () => (
  <svg {...P}><path d="M18 38 C 10 38 8 28 16 26 C 16 16 30 14 33 22 C 38 16 50 20 48 30 C 56 31 56 38 48 38 Z" /><path d="M24 44 V54 M32 44 V56 M40 44 V54" /><path d="M21 51 L24 54 L27 51 M37 51 L40 54 L43 51" /></svg>
)
export const IconoFuentes = () => (
  <svg {...P}><path d="M32 18 C 24 13 15 13 8 16 V50 C 15 47 24 47 32 52 C 40 47 49 47 56 50 V16 C 49 13 40 13 32 18 Z" /><path d="M32 18 V52 M14 24 H26 M14 31 H26 M38 24 H50 M38 31 H50" /></svg>
)
