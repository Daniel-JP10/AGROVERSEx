// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Servidor estático descartable con Range y CORS para las teselas reales (no se copian: adm2 pesa 442 MB).
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'

const RAIZ = process.env.AGROVERSEX_DATOS || process.env.DATOS || decodeURIComponent(new URL('../../../datos/procesados', import.meta.url).pathname).replace(/^\/(\w:)/, '$1')
const PUERTO = Number(process.env.PUERTO_DATOS || 5198)
const rutas = {
  '/adm1.pmtiles': 'teselas/adm1.pmtiles',
  '/adm2.pmtiles': 'teselas/adm2.pmtiles',
  '/indice.json.gz': 'indice_busqueda.json.gz',
}

http.createServer((req, res) => {
  const rel = rutas[req.url.split('?')[0]]
  const cab = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Range', 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-store' }
  if (req.method === 'OPTIONS') { res.writeHead(204, cab); return res.end() }
  if (!rel) { res.writeHead(404, cab); return res.end() }
  const f = path.join(RAIZ, rel)
  const tam = fs.statSync(f).size
  const m = /bytes=(\d+)-(\d*)/.exec(req.headers.range || '')
  if (!m) { res.writeHead(200, { ...cab, 'Content-Length': tam }); return fs.createReadStream(f).pipe(res) }
  const a = Number(m[1]), b = m[2] ? Math.min(Number(m[2]), tam - 1) : tam - 1
  res.writeHead(206, { ...cab, 'Content-Range': `bytes ${a}-${b}/${tam}`, 'Content-Length': b - a + 1 })
  fs.createReadStream(f, { start: a, end: b }).pipe(res)
}).listen(PUERTO, () => console.log('datos en', PUERTO))
