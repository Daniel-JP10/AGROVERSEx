// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'
import { ES } from './idioma'

test.use({ storageState: ES }) // asserta español y el idioma por defecto es el inglés (D-039)

// Se ejecuta con playwright.e2e.config.ts (Chrome real)
test('medir con teclado, aviso de zoom 12 y mapa interactivo', async ({ page }) => {
  await page.goto('/#/tierra')
  await page.waitForFunction(() => (window as any).__mapa?.loaded() === true)

  // Herramienta Medir desde el riel, solo con teclado
  const medir = page.locator('.riel button[aria-label="Medir"]')
  await medir.focus()
  await page.keyboard.press('Enter')
  await expect(medir).toHaveAttribute('aria-pressed', 'true')

  // Dos puntos con el botón de centro y el resultado anunciado
  const centro = page.getByRole('button', { name: 'Añadir punto en el centro' })
  await centro.focus()
  await page.keyboard.press('Enter')
  await page.keyboard.press('Enter')
  await expect(page.locator('.medir-resultado')).toContainText('2 puntos')

  // Zoom 12: aviso visible y el mapa sigue respondiendo a los controles de zoom
  await page.evaluate(() => (window as any).__mapa.jumpTo({ center: [-74, 4.6], zoom: 12 }))
  const aviso = page.getByRole('status').filter({ hasText: 'Mercator' })
  await expect(aviso).toBeVisible()
  await page.screenshot({ path: 'capturas/18-zoom12.png' })

  await page.getByRole('button', { name: 'Alejar' }).focus()
  await page.keyboard.press('Enter')
  await expect.poll(() => page.evaluate(() => (window as any).__mapa.getZoom())).toBeLessThan(12)
  await expect(aviso).toBeHidden()
})
