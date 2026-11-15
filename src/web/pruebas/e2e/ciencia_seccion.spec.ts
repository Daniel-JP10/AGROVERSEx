// asistido por SI: Claude Code (Anthropic), E2E de Ciencia y validación sobre el build estático, en los tres motores
import { expect, test } from '@playwright/test'
import { ES, medirContraste, prohibidosEnTexto } from './marco_ayuda'

const TEXTOS = ['main h1', 'main > p', '.tarjeta-hoja h2', '.tarjeta-hoja dt', '.tarjeta-hoja dd', '.tarjeta-hoja .nota', '.etiqueta-evidencia', '.limites li']

test('ciencia en inglés: ocho tarjetas, PI-D1 mundial y confianza sin dato, sin carbono; contraste AA', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 3200 })
  await page.goto('/#/ciencia')
  await expect(page.locator('[data-tarjeta]')).toHaveCount(8)
  await expect(page.locator('[data-tarjeta="pi_d1_mundo"] [data-campo="cifra"]')).toHaveText(/Not available yet/)
  await expect(page.locator('[data-tarjeta="confianza"] [data-campo="cifra"]')).toHaveText(/Not available yet/)
  await expect(page.locator('[data-tarjeta="temperatura"]')).toContainText('WMO Resolution 40')
  const texto = await page.locator('main').innerText()
  expect(texto).not.toMatch(/carbon|carbono/i)
  expect(prohibidosEnTexto(texto)).toEqual([])
  const medidas = await medirContraste(page, TEXTOS)
  expect(medidas.length).toBeGreaterThan(40)
  expect(medidas.filter((m) => m.contraste < m.minimo)).toEqual([])
})

test.describe('español', () => {
  test.use({ storageState: ES })
  test('ciencia en español con sus tarjetas', async ({ page }) => {
    await page.goto('/#/ciencia')
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Ciencia y validación')
    await expect(page.locator('[data-tarjeta="confianza"]')).toContainText('Todavía no disponible')
  })
})
