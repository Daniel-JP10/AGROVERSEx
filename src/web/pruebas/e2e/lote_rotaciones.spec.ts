// asistido por SI: Claude Code (Anthropic), E2E de El lote y Rotaciones: inglés por defecto, español, interacción, contraste AA y movimiento reducido
import { resolve } from 'node:path'
import { expect, test, type Page } from '@playwright/test'

const ORIGEN = 'http://localhost:5213'
const ES = { cookies: [], origins: [{ origin: ORIGEN, localStorage: [{ name: 'agroversex-idioma', value: 'es' }] }] }
const CAPTURAS = resolve(process.cwd(), '../../../../AGROVERSEx/repo/Docu/verificacion')

// #/lote lo monta W1; mientras no esté, #/gemelo muestra la misma sección
async function abrirLote(page: Page, lote = 'DEMO-COL-01') {
  await page.goto(`/#/lote?lote=${lote}`)
  const h = page.locator('main.lote h1')
  if (!(await h.isVisible({ timeout: 3000 }).catch(() => false))) await page.goto(`/#/gemelo?lote=${lote}`)
  await expect(page.getByTestId('estrategia-lote')).toHaveCount(3)
}

// Contraste del color del texto contra el fondo real compuesto (fondos semitransparentes mezclados hacia arriba)
async function peoresContrastes(page: Page, selector: string) {
  return page.evaluate((sel) => {
    const rgba = (s: string) => { const m = (s.match(/[\d.]+/g) ?? ['0', '0', '0', '0']).map(Number); return [m[0], m[1], m[2], m[3] ?? 1] }
    const lum = ([r, g, b]: number[]) => { const f = (c: number) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b) }
    const fondo = (el: Element | null): number[] => {
      const capas: number[][] = []
      for (let e = el; e; e = e.parentElement) { const c = rgba(getComputedStyle(e).backgroundColor); if (c[3] > 0) capas.push(c); if (c[3] >= 1) break }
      let base = rgba(getComputedStyle(document.body).backgroundColor).slice(0, 3)
      if (capas.length && capas[capas.length - 1][3] >= 1) base = capas.pop()!.slice(0, 3)
      for (const c of capas.reverse()) base = base.map((b, i) => b * (1 - c[3]) + c[i] * c[3])
      return base
    }
    const malos: string[] = []
    for (const el of Array.from(document.querySelectorAll(sel))) {
      const he = el as HTMLElement
      if (!he.innerText?.trim() || he.offsetParent === null) continue
      const cs = getComputedStyle(el)
      const c = rgba(cs.color), f = fondo(el)
      const col = c.slice(0, 3).map((v, i) => v * c[3] + f[i] * (1 - c[3]))
      const [a, b] = [lum(col), lum(f)].sort((x, y) => y - x)
      const r = (a + 0.05) / (b + 0.05)
      const grande = parseFloat(cs.fontSize) >= 24 || (parseFloat(cs.fontSize) >= 18.66 && Number(cs.fontWeight) >= 700)
      if (r < (grande ? 3 : 4.5)) malos.push(`${el.tagName}.${el.className} "${he.innerText.slice(0, 30)}" ${r.toFixed(2)}`)
    }
    return malos
  }, selector)
}
const TEXTOS = 'main h1, main h2, main h3, main p, main small, main li, main label, main th, main td, main button, main a, main legend, main figcaption, main .banda'

test.describe('El lote', () => {
  test('inglés por defecto: gemelo, voz, escenario, 3 estrategias, bloque y etiquetas del mes', async ({ page }) => {
    await abrirLote(page)
    await expect(page.locator('main.lote h1')).toContainText("Your field's twin")
    await expect(page.locator('[data-voz="agua"]')).toContainText('mm of water a year')
    await expect(page.getByText("What I'm based on")).toBeVisible()
    await expect(page.locator('#h-escenario + select option')).toHaveCount(7)
    const img = page.locator('.bloque img')
    await expect(img).toBeVisible()
    await expect.poll(() => img.evaluate((i: HTMLImageElement) => i.complete && i.naturalWidth > 0)).toBe(true)
    // El mes elegido cambia las cifras de las etiquetas
    const lluvia = page.locator('.l-etiqueta[data-variable="P"] [data-banda]')
    const antes = await lluvia.innerText()
    await page.locator('.bloque select').selectOption('3')
    await expect(lluvia).not.toHaveText(antes)
    // El escenario seco cambia las cifras de las tarjetas
    const et = page.locator('[data-indicador="et_real_mm_anio"] [data-banda]').first()
    const etAntes = await et.innerText()
    await page.locator('#h-escenario + select').selectOption('seco')
    await expect(et).not.toHaveText(etAntes)
    await page.locator('#h-escenario + select').selectOption('historico')
    await expect(page.locator('main')).not.toContainText(/t C\/ha|Lot health|Pred\.|SMAP|calibrat/i)
    expect(await peoresContrastes(page, TEXTOS)).toEqual([])
    if (test.info().project.name === 'chromium') await page.screenshot({ path: resolve(CAPTURAS, 'f3_W3_lote_1440.png') })
    await page.getByRole('tab', { name: 'Over time' }).click()
    await expect(page.locator('.grafico-banda')).toHaveCount(7)
    await expect(page.locator('.grafico-banda svg polygon.banda').first()).toBeVisible()
  })

  test('390 de ancho sin desborde horizontal', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await abrirLote(page)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true)
    if (test.info().project.name === 'chromium') await page.screenshot({ path: resolve(CAPTURAS, 'f3_W3_lote_390.png') })
  })

  test.describe('en español', () => {
    test.use({ storageState: ES })
    test('títulos y voz en español', async ({ page }) => {
      await abrirLote(page)
      await expect(page.locator('main.lote h1')).toContainText('El gemelo de tu lote')
      await expect(page.locator('[data-voz="agua"]')).toContainText('mm de agua al año')
      await expect(page.getByText('En qué me baso')).toBeVisible()
    })
  })

  test.describe('movimiento reducido', () => {
    test.use({ reducedMotion: 'reduce' })
    test('nada se anima', async ({ page }) => {
      await abrirLote(page)
      const animados = await page.evaluate(() => Array.from(document.querySelectorAll('main *')).filter((e) => {
        const cs = getComputedStyle(e)
        return (cs.animationName !== 'none' && cs.animationDuration !== '0s') || cs.transitionDuration.split(',').some((d) => parseFloat(d) > 0)
      }).length)
      expect(animados).toBe(0)
    })
  })
})

test.describe('Rotaciones', () => {
  test('inglés: fichas, gráfico con bandas, deslizadores que reordenan, N y C oculto y método real', async ({ page }) => {
    await page.goto('/#/rotaciones?lote=DEMO-COL-01')
    await expect(page.locator('.fichas .ficha').first()).toBeVisible()
    await expect(page.locator('.grafico-central polygon.banda').first()).toBeVisible()
    await expect(page.getByTestId('panel-nc')).toContainText('Not available yet')
    await expect(page.getByTestId('metodo')).toContainText('FAO-56 Penman-Monteith')
    const fichasAntes = await page.locator('.fichas').innerText()
    for (const k of ['agua', 'insumos', 'estabilidad_climatica']) await page.locator(`[data-deslizador="${k}"]`).fill('0')
    await page.locator('[data-deslizador="suelo"]').fill('5')
    await expect(page.locator('.fichas')).not.toHaveText(fichasAntes)
    await expect(page.locator('main')).not.toContainText(/t C\/ha|IMERG\/SMAP|CDL|GAEZ|ERA5/)
    await expect(page.getByTestId('fila-escenario')).toHaveCount(4)
    await page.locator('.comparador-esc select').selectOption('enso_nina')
    await expect(page.getByText('The trade-off front exists for the historical')).toBeVisible()
    expect(await peoresContrastes(page, '.tablero h2, .tablero p, .tablero small, .tablero li, .tablero label, .tablero th, .tablero td, .tablero legend')).toEqual([])
    if (test.info().project.name === 'chromium') {
      await page.locator('.comparador-esc select').selectOption('historico')
      await page.evaluate(() => window.scrollTo(0, 0))
      await page.screenshot({ path: resolve(CAPTURAS, 'f3_W3_rotaciones_1440.png') })
      await page.setViewportSize({ width: 390, height: 844 })
      await page.evaluate(() => window.scrollTo(0, 0))
      await page.screenshot({ path: resolve(CAPTURAS, 'f3_W3_rotaciones_390.png') })
    }
  })
  test.describe('en español', () => {
    test.use({ storageState: ES })
    test('títulos en español', async ({ page }) => {
      await page.goto('/#/rotaciones?lote=DEMO-USA-01')
      await expect(page.getByRole('heading', { name: 'Secuencia de la rotación' })).toBeVisible()
      await expect(page.getByTestId('panel-nc')).toContainText('Aún no disponible')
    })
  })
})
