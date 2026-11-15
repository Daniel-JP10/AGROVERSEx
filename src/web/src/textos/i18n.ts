// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { create } from 'zustand'
import { en } from './en'
import { es, type ClaveTexto } from './es'
import { conCifras } from './cifras'

export type Idioma = 'es' | 'en'
const LLAVE = 'agroversex-idioma'

// Inglés por defecto (C3, decisión del director); el español es el selector. localStorage puede fallar (modo privado, bloqueo)
const leer = (): Idioma => {
  try { return localStorage.getItem(LLAVE) === 'es' ? 'es' : 'en' } catch { return 'en' }
}
const useIdiomaStore = create<{ idioma: Idioma }>(() => ({ idioma: leer() }))

export const useIdioma = () => useIdiomaStore((s) => s.idioma)
export const idioma = () => useIdiomaStore.getState().idioma
export function alternar() {
  const nuevo: Idioma = idioma() === 'en' ? 'es' : 'en'
  useIdiomaStore.setState({ idioma: nuevo })
  try { localStorage.setItem(LLAVE, nuevo) } catch { /* sin persistencia */ }
}
// Al español le pueden faltar claves (FALTANTES_ES): cae al inglés
export const t = (clave: ClaveTexto): string => conCifras(idioma() === 'en' ? en[clave] : (es[clave] ?? en[clave]), idioma())
