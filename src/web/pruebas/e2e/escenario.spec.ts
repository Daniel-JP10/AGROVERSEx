// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'
import { ES } from './idioma'

test.use({ storageState: ES }) // asserta español y el idioma por defecto es el inglés (D-039)

// Se ejecuta con playwright.escenario.config.ts (Chrome real, datos reales)
test('pantalla dividida: segundo mapa solo al activarla, cámaras sincronizadas', async ({ page }) => {
  await page.goto('/#/tierra')
  await page.waitForFunction(() => (window as never as { __mapa?: { loaded(): boolean } }).__mapa?.loaded())
  expect(await page.evaluate(() => !!(window as never as { __mapaB?: unknown }).__mapaB)).toBe(false)
  await page.getByRole('button', { name: 'Comparar' }).click()
  await page.waitForFunction(() => !!(window as never as { __mapaB?: { loaded(): boolean } }).__mapaB?.loaded())
  await page.evaluate(() => (window as never as { __mapa: { jumpTo(o: object): void } }).__mapa.jumpTo({ center: [-74, 4.6], zoom: 4 }))
  const z = await page.evaluate(() => (window as never as { __mapaB: { getZoom(): number } }).__mapaB.getZoom())
  expect(z).toBeCloseTo(4, 1)
  await page.waitForTimeout(2500)
  await page.screenshot({ path: 'capturas/dividida.png' })
  await page.getByRole('button', { name: 'Comparar' }).click()
  expect(await page.evaluate(() => !!(window as never as { __mapaB?: unknown }).__mapaB)).toBe(false)
})

test('escenario: no sale de p25-p75 y explica por qué', async ({ page }) => {
  await page.goto('/#/tierra')
  await page.waitForFunction(() => (window as never as { __mapa?: { loaded(): boolean } }).__mapa?.loaded())
  await page.getByRole('button', { name: 'Escenario' }).click()
  await expect(page.getByText('Seleccione una unidad')).toBeVisible()
  await page.evaluate(() => (window as never as { __mapa: { jumpTo(o: object): void } }).__mapa.jumpTo({ center: [-74, 4.6], zoom: 4 }))
  await page.waitForTimeout(3000)
  const caja = (await page.locator('.mapa').boundingBox())!
  await page.mouse.click(caja.x + caja.width / 2, caja.y + caja.height / 2)
  const lluvia = page.locator('#esc-precip')
  await expect(lluvia).toBeVisible({ timeout: 20000 })
  await lluvia.focus()
  await page.keyboard.press('End') // extremo máximo: fuera de p75
  await expect(page.getByTestId('motivo-precip')).toContainText('p25-p75')
  await page.screenshot({ path: 'capturas/escenario.png' })
}
)
