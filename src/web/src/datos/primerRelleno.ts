// asistido por SI: Claude Code (Anthropic), espera a la marca del primer relleno del globo para diferir descargas grandes (presupuesto, plan v1 §a)
export const MARCA_RELLENO = 'globo-relleno'

/** Se cumple cuando el globo marca su primer relleno pintado, o al tope (sin globo o sin WebGL no se bloquea nada). */
export function trasPrimerRelleno(tope = 8000): Promise<void> {
  if (typeof performance === 'undefined' || performance.getEntriesByName(MARCA_RELLENO).length) return Promise.resolve()
  return new Promise((listo) => {
    const t = setTimeout(fin, tope)
    const obs = typeof PerformanceObserver === 'function' ? new PerformanceObserver(() => { if (performance.getEntriesByName(MARCA_RELLENO).length) fin() }) : null
    try { obs?.observe({ type: 'mark' }) } catch { /* motor sin observador de marcas: queda el tope */ }
    function fin() { clearTimeout(t); obs?.disconnect(); listo() }
  })
}
