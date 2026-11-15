// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import fs from 'node:fs'
import path from 'node:path'
import type { Plugin } from 'vite'

// Lista cerrada: solo estos nombres se sirven (nada de rutas libres).
const ARCHIVOS: Record<string, string> = {
  'adm0.pmtiles': 'teselas/adm0.pmtiles',
  'adm1.pmtiles': 'teselas/adm1.pmtiles',
  'adm2.pmtiles': 'teselas/adm2.pmtiles',
  'indice_busqueda.json.gz': 'indice_busqueda.json.gz',
}

// AGROVERSEX_DATOS apunta a datos/procesados (el worktree no trae datos/)
const raiz = () => process.env.AGROVERSEX_DATOS ?? decodeURIComponent(new URL('../../../datos/procesados', import.meta.url).pathname).replace(/^\/(\w:)/, '$1')

type Mw = (req: import('node:http').IncomingMessage, res: import('node:http').ServerResponse, next: () => void) => void

const middleware: Mw = (req, res, next) => {
  const url = (req.url ?? '').split('?')[0]
  if (!url.startsWith('/teselas/')) return next()
  const nombre = decodeURIComponent(url.slice('/teselas/'.length))
  const rel = Object.hasOwn(ARCHIVOS, nombre) ? ARCHIVOS[nombre] : undefined
  const f = rel && path.join(raiz(), rel)
  if (!f || !fs.existsSync(f)) { res.statusCode = 404; return void res.end() }
  const tam = fs.statSync(f).size
  const cab = { 'Accept-Ranges': 'bytes', 'Content-Type': 'application/octet-stream', 'Cache-Control': 'no-store' }
  const m = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range ?? '')
  if (!m) { res.writeHead(200, { ...cab, 'Content-Length': tam }); return void fs.createReadStream(f).pipe(res) }
  const a = Number(m[1]), b = m[2] ? Math.min(Number(m[2]), tam - 1) : tam - 1
  if (a > b || a >= tam) { res.writeHead(416, { 'Content-Range': `bytes */${tam}` }); return void res.end() }
  res.writeHead(206, { ...cab, 'Content-Range': `bytes ${a}-${b}/${tam}`, 'Content-Length': b - a + 1 })
  fs.createReadStream(f, { start: a, end: b }).pipe(res)
}

/** Sirve /teselas/<archivo> con soporte de Range (206) desde AGROVERSEX_DATOS, sin copiar los 500 MB. */
export function servirTeselas(): Plugin {
  return {
    name: 'servir-teselas',
    configureServer: (s) => { s.middlewares.use(middleware) },
    configurePreviewServer: (s) => { s.middlewares.use(middleware) },
  }
}
