// asistido por SI: Claude Code (Anthropic), detector de textos prohibidos compartido por las pruebas
// Decisión del director: ninguno de estos textos puede verse en la app
export const PROHIBIDOS: [string, RegExp][] = [
  ['GADM', /\bGADM\b/i],
  ['EOX', /\bEOX\b/i],
  ['cloudless', /cloudless/i],
  ['WorldClim', /WorldClim/i],
  ['GAEZ', /\bGAEZ\b/i],
  ['Köppen-Geiger 2023', /K(?:ö|o|oe)ppen[-\s]?Geiger\D{0,40}2023/i],
  // C-2: evidencia de un filtro que citaba la climatología simulada del prototipo
  ['climatología IMERG simulada', /Simulated IMERG climatology|Climatolog(?:í|i)a IMERG simulada/i],
]

// Devuelve los nombres prohibidos que aparecen; deshace los escapes \uXXXX que puede dejar el empaquetador
export function prohibidosEn(texto: string): string[] {
  const t = texto.replace(/\\u([0-9a-f]{4})/gi, (_, h) => String.fromCharCode(parseInt(h, 16))).replace(/\\x([0-9a-f]{2})/gi, (_, h) => String.fromCharCode(parseInt(h, 16)))
  return PROHIBIDOS.filter(([, re]) => re.test(t)).map(([n]) => n)
}
