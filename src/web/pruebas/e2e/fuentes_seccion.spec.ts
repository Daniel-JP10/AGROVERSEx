// asistido por SI: Claude Code (Anthropic), E2E de Fuentes sobre el build estático: tres columnas, créditos, sin rutas locales y contraste
import { expect, test } from '@playwright/test'
import { ES, medirContraste } from './marco_ayuda'

test('fuentes: tres columnas, créditos de dirección visual e IA, ninguna ruta local en pantalla; contraste AA', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 2400 })
  await page.goto('/#/fuentes')
  await expect(page.locator('.columnas-fuentes > section')).toHaveCount(3)
  await expect(page.locator('[data-credito-visual]')).toHaveText('Visual direction: Jostin Colon Ramos')
  await expect(page.locator('[data-referencias-ia]')).toContainText('generated with AI and are not used in the product')
  await page.locator('details[data-credito]').evaluateAll((ds) => ds.forEach((d) => d.setAttribute('open', '')))
  const texto = await page.locator('main').innerText()
  expect(texto).not.toMatch(/[A-Za-z]:[\/][A-Za-z]|herramientas-despliegue|\/tmp\/|\/Users\//)
  const medidas = await medirContraste(page, ['main h1', 'main > p', '.tarjeta-hoja h2', '.tarjeta-hoja h3', '.tarjeta-hoja > p', '.glosario dt', '.glosario p', '.fuentes summary', '.fuentes th', '.fuentes td'])
  expect(medidas.length).toBeGreaterThan(20)
  expect(medidas.filter((x) => x.contraste < x.minimo)).toEqual([])
})

test.describe('español', () => {
  test.use({ storageState: ES })
  test('fuentes en español', async ({ page }) => {
    await page.goto('/#/fuentes')
    await expect(page.locator('[data-credito-visual]')).toHaveText('Dirección visual: Jostin Colon Ramos')
  })
})
