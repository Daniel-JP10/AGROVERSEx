// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Se ejecuta con una config como playwright.busqueda.config.ts (testMatch panel.spec.ts)
import { expect, test } from '@playwright/test'

// Con la base de muestra real (playwright.panel.config.ts)
test('panel de región: 4 pestañas sin errores y serie con corte', async ({ page }) => {
  const errores: string[] = []
  page.on('pageerror', (e) => errores.push(e.message))
  page.on('console', (m) => m.type() === 'error' && !/favicon|Failed to load resource/.test(m.text()) && errores.push(m.text()))
  await page.goto('/#/tierra')
  const campo = page.getByRole('combobox', { name: 'Buscar' })
  await expect(campo).toHaveAttribute('placeholder', /Buscar/, { timeout: 30_000 })
  await campo.pressSequentially('Colombia', { delay: 50 })
  await page.getByRole('listbox').getByRole('option').first().click()
  const panel = page.getByRole('complementary', { name: 'Panel de región' })
  await expect(panel).toBeVisible()
  for (const t of ['Resumen', 'Series', 'Suelo', 'Fuentes']) await panel.getByRole('tab', { name: t }).click()
  await panel.getByRole('tab', { name: 'Series' }).click()
  await expect(panel.getByTestId('grafico').locator('svg')).toBeVisible()
  expect(await panel.getByTestId('grafico').locator('path[d]').count()).toBeGreaterThan(0)
  await page.screenshot({ path: 'capturas/11-panel.png' })
  expect(errores).toEqual([])
})
