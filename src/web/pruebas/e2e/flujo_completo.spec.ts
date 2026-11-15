// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'

// Con la base mundial (AGROVERSEX_SQLITE) y el índice regenerado (AGROVERSEX_DATOS)
async function buscar(page: import('@playwright/test').Page, texto: string, ctx: string) {
  const campo = page.getByRole('combobox', { name: 'Buscar' })
  await expect(campo).toHaveAttribute('placeholder', /Buscar/, { timeout: 30_000 })
  await campo.fill(texto)
  await page.getByRole('listbox').getByRole('option').filter({ hasText: new RegExp(ctx) }).first().click()
  const panel = page.getByRole('complementary', { name: 'Panel de región' })
  await expect(panel).toBeVisible()
  return panel
}

test('buscador encuentra Costa de Marfil y su panel tiene datos', async ({ page }) => {
  await page.goto('/#/tierra')
  const panel = await buscar(page, 'Costa de Marfil', 'Ivoire')
  await expect(panel.getByRole('heading', { level: 2 })).toContainText(/Marfil|Ivoire/)
  await expect(panel.locator('.dato strong').first()).not.toHaveText(/^\s*$/)
})

test('municipio de otro país (Kolkata, India) tiene dato y nunca 0 sin dato', async ({ page }) => {
  await page.goto('/#/tierra')
  const panel = await buscar(page, 'Kolkata', 'India')
  const valores = panel.locator('.dato strong')
  await expect(valores.first()).toContainText(/\d|sin dato/, { timeout: 15_000 })
  const t = await valores.allInnerTexts()
  expect(t.some((x) => /^-?\d/.test(x.trim()))).toBe(true)
  for (const x of t) if (/sin dato/.test(x)) expect(x).not.toMatch(/^\s*0(\.0+)?\s/)
})

test('zona DEMO (Mbeya): Rotaciones y Lotes; teclado en pestañas y Escape', async ({ page }) => {
  await page.goto('/#/tierra')
  const panel = await buscar(page, 'Mbeya', 'Tanzania')
  await expect(panel.getByRole('tab', { name: 'Lotes' })).toBeVisible({ timeout: 15_000 })
  await panel.getByRole('tab', { name: 'Rotaciones' }).click()
  await expect(panel.getByTestId('tarjeta').first()).toBeVisible({ timeout: 15_000 })
  await panel.getByRole('tab', { name: 'Lotes' }).click()
  await expect(panel.getByTestId('lote').first()).toBeVisible({ timeout: 15_000 })
  await panel.getByRole('tab', { name: 'Lotes' }).focus()
  await page.keyboard.press('ArrowRight')
  await expect(panel.getByRole('tab', { name: 'Fuentes' })).toHaveAttribute('aria-selected', 'true')
  await page.keyboard.press('Escape')
  await expect(panel).toHaveCount(0)
})

test('sin dato hay trama registrada y el riel se opera con teclado', async ({ page }) => {
  await page.goto('/#/tierra')
  await page.waitForFunction(() => (window as any).__mapa?.loaded())
  expect(await page.evaluate(() => (window as any).__mapa.hasImage('trama'))).toBe(true)
  const riel = page.getByRole('navigation', { name: 'Herramientas' })
  await page.keyboard.press('Tab')
  const foco = await page.evaluate(() => document.activeElement?.tagName)
  expect(foco).toBeTruthy()
  expect(await riel.getByRole('button').count()).toBeGreaterThan(0)
  await riel.getByRole('button').first().focus()
  await expect(riel.getByRole('button').first()).toBeFocused()
})
