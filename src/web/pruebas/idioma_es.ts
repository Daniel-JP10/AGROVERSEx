// asistido por SI: Claude Code (Anthropic), ayuda de pruebas: fija el español mientras corre el archivo (el idioma por defecto es el inglés, C3)
import { afterAll, beforeAll } from 'vitest'
import { alternar, idioma } from '../src/textos/i18n'

export function enEspanol() {
  beforeAll(() => { if (idioma() !== 'es') alternar() })
  afterAll(() => { if (idioma() !== 'en') alternar() })
}
