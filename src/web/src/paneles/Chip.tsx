// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
export type Procedencia = 'SIMULADO' | 'REAL·contexto' | 'FUENTE' | 'SUPUESTO' | 'PENDIENTE'
// La etiqueta de la base (real_contexto, FUENTE...) se normaliza a una de las cinco.
export const procedencia = (e: string | null | undefined): Procedencia =>
  /real/i.test(e ?? '') ? 'REAL·contexto' : /fuente/i.test(e ?? '') ? 'FUENTE' : /supuesto/i.test(e ?? '') ? 'SUPUESTO' : /pendiente/i.test(e ?? '') ? 'PENDIENTE' : 'SIMULADO'
export const Chip = ({ e }: { e: string | null | undefined }) => <span className="chip">{procedencia(e)}</span>
