// asistido por SI: Claude Code (Anthropic), cifras de datos de los textos visibles: salen de constantes del código de datos, nunca de en.ts ni es.ts

import meta from '../../public/datos/meta.json'

// Primer mes y número de meses de la serie: se leen de public/datos/meta.json (mes0, n_meses).
// No se importa de tiempo/ (frontera con las carpetas de Daniel)
const MES_INICIO = { anio: Number(meta.mes0.slice(0, 4)), mes: Number(meta.mes0.slice(5, 7)) }
const N_MESES = meta.n_meses
// Índice (desde MES_INICIO) del último mes de la línea base (2000-01 a 2015-12): definición del método, una sola fuente que usa paneles/Series.tsx
export const BASE_ULTIMO_INDICE = 191
// Fracción válida mínima para publicar un valor: UMBRAL_FRAC_VALIDA de src/simulacion/geo/serie_mensual.py (atada por prueba)
export const FRACCION_MINIMA = 0.5
// Error de la esfera de radio medio frente al elipsoide, en %: el que declara herramientas/geodesia.ts (atada por prueba)
export const ERROR_ESFERA_PCT = 0.5
// Fecha del mosaico Blue Marble del fondo: título oficial de la capa GIBS (datos/evidencia/gibs_fondo.md, atada por prueba)
export const FONDO = { anio: 2004, mes: 8 }

const anioDe = (indice: number) => MES_INICIO.anio + Math.floor((MES_INICIO.mes - 1 + indice) / 12)
const dosDig = (n: number) => String(n).padStart(2, '0')
const numero = (n: number, lang: string) => new Intl.NumberFormat(lang, { maximumFractionDigits: 2 }).format(n)

/** Valor de cada hueco de cifra de datos para el idioma dado; undefined si el nombre no es una cifra conocida. */
export function cifra(nombre: string, lang: string): string | undefined {
  switch (nombre) {
    case 'anios_serie': return `${anioDe(0)}-${anioDe(N_MESES - 1)}`
    case 'anios_base': return `${anioDe(0)}-${anioDe(BASE_ULTIMO_INDICE)}`
    case 'fecha_inicio_serie': return `${MES_INICIO.anio}-${dosDig(MES_INICIO.mes)}-01`
    case 'fraccion_minima': return numero(FRACCION_MINIMA, lang)
    case 'error_esfera': return numero(ERROR_ESFERA_PCT, lang)
    case 'fondo_fecha': return new Intl.DateTimeFormat(lang, { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(Date.UTC(FONDO.anio, FONDO.mes - 1, 1))
    default: return undefined
  }
}

/** Sustituye en el texto los huecos que son cifras de datos; los demás quedan intactos para rellenar() del recorrido. */
export const conCifras = (texto: string, lang: string): string => texto.replace(/\{(\w+)\}/g, (m, n: string) => cifra(n, lang) ?? m)
