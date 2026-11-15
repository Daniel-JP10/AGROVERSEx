// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'
import { ES } from './idioma'

test.use({ storageState: ES }) // asserta español y el idioma por defecto es el inglés (D-039)

test('lotes: zona DEMO con ventana, sensor, riesgos y banco', async ({ page }) => {
  await page.goto('/src/paneles/lotes/demo.html')
  await expect(page.getByTestId('aviso-sim')).toContainText('SIMULADO')
  await expect(page.getByTestId('lote').first()).toBeVisible()
  await expect(page.getByTestId('ventana')).toBeVisible()
  await expect(page.getByTestId('sensor-grafico').locator('svg').first()).toBeVisible()
  await expect(page.getByTestId('riesgo')).toHaveCount(3)
  await expect(page.getByTestId('riesgo').nth(0)).toContainText('PENDIENTE')
  await expect(page.getByTestId('riesgo').nth(1)).toContainText('contexto de SMAP 9 km, no del lote')
  await page.getByRole('button', { name: 'Probar' }).click()
  await expect(page.getByRole('status')).toContainText('no se guardó nada')
  await page.screenshot({ path: 'capturas/16-lotes.png', fullPage: true })
})
