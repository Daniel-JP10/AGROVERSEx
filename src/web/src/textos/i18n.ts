// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { create } from 'zustand'
import { en } from './en'
import { es, type ClaveTexto } from './es'

export type Idioma = 'es' | 'en'
const LLAVE = 'agroversex-idioma'

// localStorage puede fallar (modo privado, bloqueo)
const leer = (): Idioma => {
  try { return localStorage.getItem(LLAVE) === 'en' ? 'en' : 'es' } catch { return 'es' }
}
const useIdiomaStore = create<{ idioma: Idioma }>(() => ({ idioma: leer() }))

export const useIdioma = () => useIdiomaStore((s) => s.idioma)
export const idioma = () => useIdiomaStore.getState().idioma
export function alternar() {
  const nuevo: Idioma = idioma() === 'es' ? 'en' : 'es'
  useIdiomaStore.setState({ idioma: nuevo })
  try { localStorage.setItem(LLAVE, nuevo) } catch { /* sin persistencia */ }
}
// Al español le pueden faltar claves (FALTANTES_ES): cae al inglés
export const t = (clave: ClaveTexto): string => (idioma() === 'en' ? en[clave] : (es[clave] ?? en[clave]))
