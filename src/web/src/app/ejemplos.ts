// asistido por SI: Claude Code (Anthropic), carga de ejemplos detrás de la bandera VITE_EJEMPLOS (contrato web_componentes §9)
// Vite sustituye la bandera al compilar: sin ella el import dinámico desaparece de la versión pública
export const cargarEjemplos = () => (import.meta.env.VITE_EJEMPLOS === '1' ? import('../ejemplos') : Promise.resolve(null))
