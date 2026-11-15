// asistido por SI: Claude Code (Anthropic), E2E de Datos abiertos sobre el build estático: tarjetas del manifiesto, enlaces y contraste
import { expect, test } from '@playwright/test'
import { ES, medirContraste } from './marco_ayuda'

test('datos abiertos: una tarjeta por archivo del manifiesto, descarga real y contraste AA', async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 3600 })
  const m = await (await request.get('/datos/manifiesto.json')).json() as { archivos: Record<string, unknown> }
  await page.goto('/#/datos')
  await expect(page.locator('[data-archivo]')).toHaveCount(Object.keys(m.archivos).length)
  await expect(page.locator('[data-nota="gemelo"]')).toContainText('Model simulation')
  await expect(page.locator('[data-nota="teselas"] a')).toHaveAttribute('href', 'https://github.com/Daniel-JP10/agroversex-teselas')
  // la descarga de una serie apunta a un archivo que existe en el build
  const href = await page.locator('[data-archivo="COL/precip_0.json.gz"] a.boton').getAttribute('href')
  expect((await request.get(href!)).status()).toBe(200)
  const medidas = await medirContraste(page, ['main h1', 'main > p', '.tarjeta-hoja h2', '.tarjeta-hoja dt', '.tarjeta-hoja dd', '.tarjeta-hoja p', '.datos .boton'])
  expect(medidas.length).toBeGreaterThan(40)
  expect(medidas.filter((x) => x.contraste < x.minimo)).toEqual([])
})

test.describe('español', () => {
  test.use({ storageState: ES })
  test('datos abiertos en español', async ({ page }) => {
    await page.goto('/#/datos')
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Datos abiertos')
    await expect(page.locator('[data-nota="gemelo"]')).toContainText('Simulación del modelo')
  })
})
