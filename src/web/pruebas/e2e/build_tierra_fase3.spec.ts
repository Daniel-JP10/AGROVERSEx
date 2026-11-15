// asistido por SI: Claude Code (Anthropic), E2E de Earth en fase 3 sobre el build estático: Soil sin base simulada, lotes DEMO, leyenda, reduced-motion y presupuesto (plan v2 §3 y §7.5); leyenda plegable con versiones agrupadas (S1w)
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { gunzipSync } from 'node:zlib'
import { expect, test, type Page } from '@playwright/test'

// Unidad fuera de los lotes DEMO: el departamento de Vichada (Colombia), del índice de búsqueda
const FUERA = 'COL-ADM1-13589884B14692588923622'
// Claves de la base simulada de suelo del prototipo (src/simulacion/suelo.py y escribir_sqlite.py)
const CLAVES_SIMULADAS = ['soc_0_30', 'phh2o_0_30', 'clay_0_30', 'sand_0_30', 'silt_0_30', 'bdod_0_30', 'cec_0_30', 'nitrogen_0_30', 'elev_media', 'elev_min', 'elev_max', 'erosion_p50', 'dias_suelo_expuesto', 'suelo_metodo', '"estatico"']
const IDIOMAS = [{ idioma: 'en', soil: 'Soil', texto: 'Not available yet', lote: 'Select a lot' }, { idioma: 'es', soil: 'Suelo', texto: 'Aún no disponible', lote: 'Elige un lote' }] as const
const DIST = join(process.cwd(), 'dist')

// Idioma sembrado antes de cargar (el puerto 5198 no es el de idioma.ts)
const conIdioma = (page: Page, idioma: string) => page.addInitScript((i) => { try { localStorage.setItem('agroversex-idioma', i) } catch { /* sin almacenamiento */ } }, idioma)

// Todos los JSON de dist, descomprimidos si vienen en gzip; las teselas binarias no son JSON
function jsonDeDist(dir = DIST): { ruta: string; texto: string }[] {
  return readdirSync(dir).flatMap((n) => {
    const r = join(dir, n)
    if (statSync(r).isDirectory()) return jsonDeDist(r)
    if (n.endsWith('.json')) return [{ ruta: r, texto: readFileSync(r, 'utf-8') }]
    if (n.endsWith('.json.gz')) return [{ ruta: r, texto: gunzipSync(readFileSync(r)).toString('utf-8') }]
    return []
  })
}

for (const L of IDIOMAS) {
  test.describe(`idioma ${L.idioma}`, () => {
    test.beforeEach(async ({ page }) => conIdioma(page, L.idioma))

    test('Soil fuera de los lotes dice que aún no hay dato y no trae la base simulada', async ({ page }) => {
      await page.goto(`/#/tierra?unidad=${FUERA}`)
      const panel = page.getByRole('complementary')
      await expect(panel).toBeVisible({ timeout: 60_000 })
      await panel.getByRole('tab', { name: L.soil, exact: true }).click()
      const suelo = panel.getByTestId('suelo')
      await expect(suelo).toContainText(L.texto)
      // ninguna cifra en la pestaña
      expect(await suelo.innerText()).not.toMatch(/\d/)
      const html = await page.content()
      for (const c of CLAVES_SIMULADAS) expect(html, c).not.toContain(c.replace(/"/g, ''))
    })

    test('Select a lot: líneas a los dos lotes DEMO y vuelo al punto real con paso a #/lote', async ({ page }) => {
      await page.goto('/#/tierra')
      const hoja = page.getByRole('group', { name: L.lote })
      await expect(hoja.getByRole('button')).toHaveCount(2, { timeout: 60_000 })
      const lineas = page.locator('svg.lotes-lineas')
      await expect(lineas).toHaveAttribute('aria-hidden', 'true')
      await expect(lineas.locator('line')).toHaveCount(2)
      // el centro al terminar el vuelo queda en el punto de lotes_demo.json
      await page.evaluate(() => { const m = (window as any).__mapa; m.once('moveend', () => { (window as any).__centro = m.getCenter() }) })
      await hoja.locator('button[data-lote="DEMO-COL-01"]').click()
      await expect(page).toHaveURL(/#\/lote\?lote=DEMO-COL-01$/, { timeout: 15_000 })
      const c = await page.evaluate(() => (window as any).__centro)
      expect(c.lat).toBeCloseTo(0.842, 2)
      expect(c.lng).toBeCloseTo(-77.661, 2)
    })

    test('leyenda en hoja con producto, versión y estado de meta.json y la trama sin dato', async ({ page }) => {
      const meta = JSON.parse(readFileSync(join(DIST, 'datos/meta.json'), 'utf-8'))
      await page.goto('/#/tierra')
      const ley = page.getByRole('group', { name: /legend|leyenda/i })
      await expect(ley).toBeVisible({ timeout: 60_000 })
      // S1w: la leyenda es plegable; se abre antes de comprobar
      const det = ley.locator(':scope > details')
      if (await det.count()) await det.evaluate((e) => { (e as HTMLDetailsElement).open = true })
      // Cada producto con su nombre y cada una de sus versiones: las del mismo producto van agrupadas con "/" en una línea
      for (const p of meta.variables.precip.productos as { producto: string; version: string }[]) {
        const linea = ley.locator('.chip').filter({ hasText: p.producto })
        await expect(linea.first()).toBeVisible()
        const textos = await linea.allInnerTexts()
        const versiones = textos.flatMap((x) => x.slice(x.indexOf(p.producto) + p.producto.length).trim().split(' ')[0].split('/'))
        expect(versiones, p.producto).toContain(p.version)
      }
      await expect(ley).toContainText(/No product data|Sin dato del producto/)
      await expect(page.getByRole('slider')).toBeVisible()
    })
  })
}

test('Soil: ningún JSON de dist trae claves de la base simulada de suelo', () => {
  const archivos = jsonDeDist()
  expect(archivos.length).toBeGreaterThan(0)
  for (const { ruta, texto } of archivos) for (const c of CLAVES_SIMULADAS) expect(texto, `${ruta}: ${c}`).not.toContain(c)
})

test.describe('reduced-motion', () => {
  test.use({ reducedMotion: 'reduce' })
  test('sin órbitas y salto directo (jumpTo) al lote', async ({ page }) => {
    await page.goto('/#/tierra')
    const boton = page.locator('button[data-lote="DEMO-USA-01"]')
    await expect(boton).toBeVisible({ timeout: 60_000 })
    const t0 = Date.now()
    await boton.click()
    await expect(page).toHaveURL(/#\/lote\?lote=DEMO-USA-01$/, { timeout: 2_000 })
    expect(Date.now() - t0).toBeLessThan(2_000) // flyTo dura 2,4 s; jumpTo es inmediato
  })
})

// Director 14:28: sin órbitas, y ninguna hoja (búsqueda, leyenda, atribución, lotes, tiempo) sale del viewport
for (const vp of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
  test(`hojas dentro del viewport y sin órbitas a ${vp.width}×${vp.height}`, async ({ page }) => {
    await page.setViewportSize(vp)
    await page.goto('/#/tierra')
    await expect(page.locator('.hoja-tiempo')).toBeVisible({ timeout: 60_000 })
    await page.waitForTimeout(1500)
    await expect(page.locator('.orbitas, .orbita')).toHaveCount(0)
    const fuera = await page.evaluate(() => {
      const sel = '.hoja, .maplibregl-ctrl-attrib, .busqueda, .leyenda, [class*="atribucion"]'
      return [...document.querySelectorAll(sel)].filter((e) => {
        const r = e.getBoundingClientRect()
        if (r.width === 0 || r.height === 0 || getComputedStyle(e).visibility === 'hidden') return false
        return r.left < -1 || r.top < -1 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1
      }).map((e) => `${e.className}`)
    })
    expect(fuera).toEqual([])
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    // Atribución con el tema (no la caja blanca de MapLibre) y cerrada al cargar
    const at = page.locator('.maplibregl-ctrl-attrib')
    expect(await at.evaluate((e) => getComputedStyle(e).backgroundColor)).not.toBe('rgb(255, 255, 255)')
    await expect(at).not.toHaveClass(/maplibregl-compact-show/, { timeout: 30_000 })
  })
}

test('presupuesto: primer relleno pintado del globo ≤ 6 s con red lenta (9 Mbit/s, 150 ms)', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'la limitación de red por CDP solo existe en Chromium')
  const cdp = await page.context().newCDPSession(page)
  await cdp.send('Network.enable')
  await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: (9e6 / 8), uploadThroughput: (9e6 / 8) })
  await page.goto('/#/tierra')
  const ms = await page.waitForFunction(() => performance.getEntriesByName('globo-relleno')[0]?.startTime, null, { timeout: 30_000, polling: 100 })
  const valor = Number(await ms.jsonValue())
  console.log(`primer relleno pintado: ${Math.round(valor)} ms`)
  expect(valor).toBeLessThanOrEqual(6000)
})

// Contraste AA medido sobre el fondo real: se oculta el texto (y la muestra decorativa), se captura su caja y se toma el píxel más desfavorable
const TEXTOS = ['.hoja-lotes h2', '.hoja-lotes p', '.hoja-lotes button', '.leyenda b', '.leyenda dt', '.leyenda dd', '.leyenda .hueco', '.leyenda .extremos', '.hoja-tiempo .ext', '.hoja-tiempo [data-testid="mes"]']
test('contraste AA de los textos de las hojas sobre el fondo real', async ({ page }) => {
  await page.goto('/#/tierra')
  await expect(page.locator('.hoja-lotes button')).toHaveCount(2, { timeout: 60_000 })
  await page.waitForTimeout(2000)
  const fallos: string[] = []
  for (const sel of TEXTOS) {
    for (const el of await page.locator(sel).all()) {
      const { color, grande } = await el.evaluate((e) => { const s = getComputedStyle(e); return { color: s.color, grande: parseFloat(s.fontSize) >= 24 || (parseFloat(s.fontSize) >= 18.66 && Number(s.fontWeight) >= 700) } })
      await el.evaluate((e) => { (e as HTMLElement).style.setProperty('color', 'transparent', 'important'); e.querySelectorAll('*').forEach((h) => (h as HTMLElement).style.setProperty('color', 'transparent', 'important')); e.querySelectorAll('[aria-hidden="true"]').forEach((h) => (h as HTMLElement).style.setProperty('visibility', 'hidden')) })
      const png = await el.screenshot()
      await el.evaluate((e) => { (e as HTMLElement).style.removeProperty('color'); e.querySelectorAll('*').forEach((h) => { (h as HTMLElement).style.removeProperty('color'); (h as HTMLElement).style.removeProperty('visibility') }) })
      const razon = await page.evaluate(async ({ b64, color }) => {
        const lum = (r: number, g: number, b: number) => { const f = (c: number) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b) }
        const [r, g, b] = color.match(/[\d.]+/g)!.map(Number)
        const lt = lum(r, g, b)
        const img = new Image(); img.src = `data:image/png;base64,${b64}`; await img.decode()
        const c = document.createElement('canvas'); c.width = img.width; c.height = img.height
        const x = c.getContext('2d')!; x.drawImage(img, 0, 0)
        const d = x.getImageData(0, 0, c.width, c.height).data
        let peor = Infinity
        for (let i = 0; i < d.length; i += 4) { const lf = lum(d[i], d[i + 1], d[i + 2]); const q = (Math.max(lt, lf) + 0.05) / (Math.min(lt, lf) + 0.05); if (q < peor) peor = q }
        return peor
      }, { b64: png.toString('base64'), color })
      if (razon < (grande ? 3 : 4.5)) fallos.push(`${sel}: ${razon.toFixed(2)}`)
    }
  }
  expect(fallos).toEqual([])
})
