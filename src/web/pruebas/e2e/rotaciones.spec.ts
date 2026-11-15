// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'

test('comparador: Corn Belt con 3 estrategias y sus 5 bloques', async ({ page }) => {
  await page.goto('/src/paneles/comparador/demo.html')
  await expect(page.getByTestId('tarjeta')).toHaveCount(3)
  for (const b of ['porque', 'evidencia', 'beneficios', 'vacios', 'riesgos']) await expect(page.locator(`[data-bloque=${b}]`)).toHaveCount(3)
  await expect(page.getByTestId('etiqueta')).toHaveText('FUENTE')
  await expect(page.getByTestId('rinde-menos')).toBeVisible()
  await page.screenshot({ path: 'capturas/15-rotaciones.png', fullPage: true })
})
