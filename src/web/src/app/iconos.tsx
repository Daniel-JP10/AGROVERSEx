// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { ReactNode } from 'react'

// Iconos propios de 24 px (trazo 1,75), dibujados para AGROVERSEx
const trazos: Record<string, ReactNode> = {
  capas: <><path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="m3 12 9 5 9-5" /><path d="m3 16 9 5 9-5" /></>,
  filtros: <path d="M4 5h16l-6 8v6l-4-2v-4L4 5Z" />,
  medir: <><path d="m3 17 14-14 4 4L7 21l-4-4Z" /><path d="m7 13 2 2M10 10l1.5 1.5M13 7l2 2" /></>,
  comparar: <><rect x="3" y="4" width="8" height="16" rx="1.5" /><rect x="13" y="4" width="8" height="16" rx="1.5" /></>,
  escenario: <><path d="M4 7h10M18 7h2M4 17h2M10 17h10" /><circle cx="16" cy="7" r="2" /><circle cx="8" cy="17" r="2" /></>,
  fuentes: <><path d="M5 4h10a4 4 0 0 1 4 4v12H9a4 4 0 0 1-4-4V4Z" /><path d="M9 9h6M9 13h6" /></>,
}

export function Icono({ id }: { id: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {trazos[id]}
    </svg>
  )
}
