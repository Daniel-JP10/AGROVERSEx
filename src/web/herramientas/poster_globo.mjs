// asistido por SI: Claude Code (Anthropic), póster del globo para la entrada: captura del globo en reposo sobre el build estático (plan v1 §a)
// Uso, desde src/web y con dist ya construido y desplegado (teselas incluidas):
//   node herramientas/poster_globo.mjs
// Escribe public/portada/globo.webp (≤ 400 px) y public/portada/globo.manifiesto.json con su SHA-256.
// Solo nuestros datos (Colombia, IMERG del mes inicial) sobre el fondo Blue Marble de GIBS, ya atribuido en la app.
import { spawn } from 'node:child_process'
import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync } from 'node:fs'
import { chromium } from '@playwright/test'

const PUERTO = 5199
const LADO = 400 // px del póster
const VISTA = { center: [-74, 4], zoom: 1.6 } // Colombia al frente, mismo zoom de la vista inicial
const SALIDA = 'public/portada/globo.webp'

const servidor = spawn(process.execPath, ['pruebas/build_servidor.mjs', 'dist', String(PUERTO)], { stdio: 'ignore' })
try {
  // Espera a que el servidor responda (hasta 10 s)
  for (let i = 0; i < 50; i++) { try { if ((await fetch(`http://localhost:${PUERTO}/`)).ok) break } catch { /* aún no escucha */ } await new Promise((r) => setTimeout(r, 200)) }
  const nav = await chromium.launch()
  // Ventana fija y escala 1: la captura no depende de la pantalla de quien corre el script
  const pag = await nav.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1, reducedMotion: 'reduce' })
  await pag.goto(`http://localhost:${PUERTO}/#/tierra`)
  pag.on('console', (m) => { if (m.type() === 'error') console.error('navegador:', m.text()) })
  await pag.waitForFunction(() => performance.getEntriesByName('globo-relleno').length > 0, null, { timeout: 120_000 })
  // Vista fija y espera al reposo (todas las teselas y el relleno aplicados)
  await pag.evaluate((v) => new Promise((listo) => { const m = window.__mapa; m.jumpTo(v); m.once('idle', listo) }), VISTA)
  await pag.waitForTimeout(1500)
  await pag.evaluate(() => new Promise((listo) => { const m = window.__mapa; if (m.loaded()) listo(); else m.once('idle', listo) }))
  // Solo el globo: fuera estrellas, hojas, controles y textos
  await pag.addStyleTag({ content: 'body * { visibility: hidden !important } .globo, .globo .mapa, .globo .mapa *, .globo .halo { visibility: visible !important } .maplibregl-control-container { display: none !important }' })
  await pag.waitForTimeout(300)
  const caja = await pag.locator('.globo .mapa').boundingBox()
  // Radio del globo a este zoom (globo/atmosfera.ts: 0,84 · 512 · 2^z / 2π) más el brillo
  const r = Math.ceil((0.84 * 512 * 2 ** VISTA.zoom) / (2 * Math.PI) * 1.12)
  const cx = caja.x + caja.width / 2, cy = caja.y + caja.height / 2
  const png = await pag.screenshot({ clip: { x: cx - r, y: cy - r, width: 2 * r, height: 2 * r }, omitBackground: true })
  // WebP en el propio Chromium: recorte circular con fondo transparente y escala a LADO
  const webp = await pag.evaluate(async ({ b64, lado }) => {
    const img = new Image(); img.src = `data:image/png;base64,${b64}`; await img.decode()
    const c = document.createElement('canvas'); c.width = c.height = lado
    const g = c.getContext('2d')
    g.beginPath(); g.arc(lado / 2, lado / 2, lado / 2, 0, 2 * Math.PI); g.clip()
    g.drawImage(img, 0, 0, lado, lado)
    return c.toDataURL('image/webp', 0.82).split(',')[1]
  }, { b64: png.toString('base64'), lado: LADO })
  await nav.close()
  const bytes = Buffer.from(webp, 'base64')
  if (bytes.subarray(8, 12).toString() !== 'WEBP') throw new Error('el navegador no devolvió WebP')
  mkdirSync('public/portada', { recursive: true })
  writeFileSync(SALIDA, bytes)
  const manifiesto = {
    archivo: 'globo.webp', sha256: createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length, ancho: LADO, alto: LADO,
    script: 'src/web/herramientas/poster_globo.mjs', vista: VISTA, datos: 'datos/COL (IMERG, mes inicial de la app)',
    fondo: 'Blue Marble, NASA GIBS (atribuido en la app)', nota: 'Captura de WebGL: el SHA-256 identifica esta salida; otra GPU o versión del navegador puede dar bytes distintos',
  }
  writeFileSync('public/portada/globo.manifiesto.json', JSON.stringify(manifiesto, null, 1) + '\n')
  console.log(JSON.stringify(manifiesto))
} finally {
  servidor.kill()
}
