// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'

// Se ejecuta con playwright.busqueda.config.ts
test('Colombia › Meta › Acacías por búsqueda, subida por miga y Escape', async ({ page }) => {
  await page.goto('/#/tierra')
  const campo = page.getByRole('combobox', { name: 'Buscar' })
  await expect(campo).toHaveAttribute('placeholder', /Buscar/, { timeout: 30_000 })
  await campo.fill('Acacias')
  const opcion = page.getByRole('option').filter({ hasText: 'Meta' }).first()
  await expect(opcion).toContainText('Colombia')
  await campo.press('ArrowDown'); await campo.press('ArrowUp')
  await opcion.click()
  const miga = page.getByRole('navigation', { name: 'Ubicación' })
  await expect(miga).toContainText('Colombia › Meta › Acacías')
  await page.screenshot({ path: 'capturas/10-meta.png' })
  await miga.getByRole('button', { name: 'Meta' }).click() // sube un nivel
  await expect(miga).toContainText('Colombia › Meta')
  await expect(miga).not.toContainText('Acacías')
  await page.keyboard.press('Escape')
  await expect(page.getByRole('complementary', { name: 'Panel de región' })).toHaveCount(0)
})
