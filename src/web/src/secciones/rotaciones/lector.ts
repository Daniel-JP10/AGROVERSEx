// asistido por SI: Claude Code (Anthropic), lectura del paquete estático del gemelo v1.2 (copiado a public/gemelo/) y de lotes_demo.json
import { useEffect, useState } from 'react'
import { useIdioma, type Idioma } from '../../textos/i18n'
import type { Fuente, SalidaOptimizacion } from './gemelo'
import type { Catalogo } from './textosGemelo'
import { corregirCatalogoEn } from './correccionEn'

// gemelo_api v1.1 §5: el id viene de la ruta, así que se valida antes de armar ninguna URL
export const LOTE_DEMO = /^DEMO-[A-Z]{3}-\d{2}$/
// Rutas que da indice.json, relativas a public/gemelo/ (copia de datos/publicos/gemelo/); sin subir de carpeta
const RUTA_SEGURA = /^(?!.*\.\.)[\w+\-/.]+\.json$/
const GEMELO = 'gemelo/'

type Pedir = (url: string) => Promise<Response>

async function json<T>(pedir: Pedir, ruta: string): Promise<T> {
  const r = await pedir(import.meta.env.BASE_URL + ruta)
  if (!r.ok) throw new Error(`HTTP ${r.status} ${ruta}`)
  return r.json() as Promise<T>
}

interface LotesDemo { lotes?: { lote_id: string }[] }
interface Indice { textos?: Partial<Record<Idioma, string>>; lotes?: { lote_id: string; escenarios?: Record<string, { optimizacion?: string } | undefined> }[] }

/** El lote debe estar en lotes_demo.json y en indice.json; si falta algo, sin_dato: nunca se inventa. */
export async function cargarGemelo(lote: string, idioma: Idioma, pedir: Pedir = (u) => fetch(u), escenario = 'historico'): Promise<Fuente> {
  // Vite sustituye la bandera al compilar: sin VITE_EJEMPLOS el import del ejemplo desaparece de la versión pública
  if (import.meta.env.VITE_EJEMPLOS === '1') {
    const [doc, textos] = await Promise.all([import('./ejemplo_gemelo.json'), import('./ejemplo_textos_gemelo.json')])
    return { estado: 'listo', origen: 'ejemplo', doc: doc.default as unknown as SalidaOptimizacion, catalogo: (textos.default as Record<Idioma, Catalogo>)[idioma] }
  }
  if (!LOTE_DEMO.test(lote)) return { estado: 'sin_dato' }
  try {
    const lotes = await json<LotesDemo>(pedir, 'datos/lotes_demo.json')
    if (!lotes.lotes?.some((l) => l.lote_id === lote)) return { estado: 'sin_dato' }
    const indice = await json<Indice>(pedir, `${GEMELO}indice.json`)
    const ruta = indice.lotes?.find((l) => l.lote_id === lote)?.escenarios?.[escenario]?.optimizacion
    const rutaTextos = indice.textos?.[idioma]
    if (!ruta || !RUTA_SEGURA.test(ruta) || !rutaTextos || !RUTA_SEGURA.test(rutaTextos)) return { estado: 'sin_dato' }
    const [doc, catalogo] = await Promise.all([json<SalidaOptimizacion>(pedir, GEMELO + ruta), json<Catalogo>(pedir, GEMELO + rutaTextos)])
    if (!doc?.linea_base || !Array.isArray(doc.frente)) return { estado: 'sin_dato' }
    return { estado: 'listo', origen: 'modelo', doc, catalogo: idioma === 'en' ? corregirCatalogoEn(catalogo) : catalogo }
  } catch {
    return { estado: 'sin_dato' }
  }
}

/** Sin lote no se pide nada; con lote devuelve cargando hasta que llega la salida. */
export function useFuente(lote: string | undefined, escenario = 'historico'): Fuente {
  const idioma = useIdioma()
  const [hecho, setHecho] = useState<{ clave: string; fuente: Fuente } | null>(null)
  const clave = `${lote}|${idioma}|${escenario}`
  useEffect(() => {
    if (!lote) return
    let vivo = true
    void cargarGemelo(lote, idioma, undefined, escenario).then((fuente) => { if (vivo) setHecho({ clave, fuente }) })
    return () => { vivo = false }
  }, [lote, idioma, clave, escenario])
  if (!lote) return { estado: 'sin_lote' }
  return hecho?.clave === clave ? hecho.fuente : { estado: 'cargando' }
}
