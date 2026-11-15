// asistido por SI: Claude Code (Anthropic), servidor estático mínimo con Range para probar dist/ sin Vite ni API; fase 3: gzip de texto como el alojamiento
import fs from 'node:fs'
import http from 'node:http'
import path from 'node:path'
import zlib from 'node:zlib'

const [raiz = 'dist', puerto = '5198'] = process.argv.slice(2)
const TIPOS = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.webp': 'image/webp' }
const base = path.resolve(raiz)

http.createServer((req, res) => {
  const url = decodeURIComponent((req.url ?? '/').split('?')[0])
  const f = path.join(base, url === '/' ? 'index.html' : url)
  // Ningún /api: este servidor solo sirve archivos, como un alojamiento estático
  if (!f.startsWith(base) || !fs.existsSync(f) || !fs.statSync(f).isFile()) { res.statusCode = 404; return void res.end() }
  const tam = fs.statSync(f).size
  const cab = { 'Accept-Ranges': 'bytes', 'Content-Type': TIPOS[path.extname(f)] ?? 'application/octet-stream' }
  const m = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range ?? '')
  // Texto sin Range: gzip si el navegador lo acepta, como hace un alojamiento estático (los .gz y las teselas van tal cual)
  if (!m && /^(text\/|application\/json)/.test(cab['Content-Type']) && /gzip/.test(req.headers['accept-encoding'] ?? '')) {
    res.writeHead(200, { ...cab, 'Content-Encoding': 'gzip', Vary: 'Accept-Encoding' })
    return void fs.createReadStream(f).pipe(zlib.createGzip()).pipe(res)
  }
  if (!m) { res.writeHead(200, { ...cab, 'Content-Length': tam }); return void fs.createReadStream(f).pipe(res) }
  const a = Number(m[1]), b = m[2] ? Math.min(Number(m[2]), tam - 1) : tam - 1
  if (a > b || a >= tam) { res.writeHead(416, { 'Content-Range': `bytes */${tam}` }); return void res.end() }
  res.writeHead(206, { ...cab, 'Content-Range': `bytes ${a}-${b}/${tam}`, 'Content-Length': b - a + 1 })
  fs.createReadStream(f, { start: a, end: b }).pipe(res)
}).listen(Number(puerto), () => console.log(`dist en http://localhost:${puerto}`))
