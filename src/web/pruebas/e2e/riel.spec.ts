// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'
import { contraste } from '../../src/app/contraste'

// Se ejecuta con playwright.e2e.config.ts (Chrome real)
test('riel: sin texto cortado, teclado y foco visible', async ({ page }) => {
  await page.goto('/#/tierra')
  const botones = page.locator('.riel button')
  const n = await botones.count()
  expect(n).toBe(6)

  const cortados = await page.locator('.riel .etq').evaluateAll((els) => els.filter((e) => e.scrollWidth > e.clientWidth).length)
  expect(cortados).toBe(0)

  await botones.first().focus()
  for (let i = 0; i < n; i++) {
    const b = botones.nth(i)
    await expect(b).toBeFocused()
    const anillo = await b.evaluate((e) => {
      const s = getComputedStyle(e)
      return { color: s.outlineColor, ancho: parseFloat(s.outlineWidth), fondo: getComputedStyle(document.body).backgroundColor }
    })
    expect(anillo.ancho).toBeGreaterThanOrEqual(1.5) // 2 px CSS, Chrome redondea con el DPI
    const hex = (c: string) => '#' + (c.match(/\d+/g) ?? []).slice(0, 3).map((x) => (+x).toString(16).padStart(2, '0')).join('')
    expect(contraste(hex(anillo.color), hex(anillo.fondo))).toBeGreaterThanOrEqual(3)
    await page.keyboard.press('Enter')
    await expect(b).toHaveAttribute('aria-pressed', 'true')
    await page.keyboard.press('Space') // alterna: vuelve a desactivar
    await expect(b).toHaveAttribute('aria-pressed', 'false')
    await page.keyboard.press('Tab')
  }
})

test('captura del riel a zoom 1 y zoom 10', async ({ page }) => {
  await page.goto('/#/tierra')
  await page.waitForTimeout(2500) // teselas y globo
  await page.locator('.riel button').nth(1).focus()
  await page.screenshot({ path: 'capturas/09-riel.png' })
  await page.evaluate(() => (window as any).__mapa.jumpTo({ center: [-74, 4.6], zoom: 10 }))
  await page.waitForTimeout(3500)
  await page.screenshot({ path: 'capturas/09-riel-z10.png' })
})
