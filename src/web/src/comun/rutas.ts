// asistido por SI: Claude Code, ruta de archivos públicos con el prefijo de despliegue (D-014, T-D9)
// Teselas, índice y datos estáticos se piden con BASE_URL; así la app vive bajo /repo/ en un alojamiento estático.
// D-014: la versión pública no tiene server/. Las vistas que aún leen /api (ENSO, filtros, rotaciones) no piden nada sin API
// hasta que T-D7 y Web publiquen su archivo estático. Una variable de entorno de Vite la enciende en desarrollo local.
export const HAY_API: boolean = import.meta.env.VITE_HAY_API === '1'
export const rutaPublica = (p: string): string => import.meta.env.BASE_URL.replace(/\/?$/, '/') + p.replace(/^\//, '')
