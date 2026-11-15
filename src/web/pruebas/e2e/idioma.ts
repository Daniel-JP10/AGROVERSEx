// asistido por SI: Claude Code (Anthropic), ayuda de e2e: siembra el idioma guardado de la app (por defecto es el inglés, C3)
// El origen es el de playwright.e2e.config.ts (puerto 5197)
export const guardado = (idioma: 'es' | 'en') => ({ cookies: [], origins: [{ origin: 'http://localhost:5197', localStorage: [{ name: 'agroversex-idioma', value: idioma }] }] })
export const ES = guardado('es')
