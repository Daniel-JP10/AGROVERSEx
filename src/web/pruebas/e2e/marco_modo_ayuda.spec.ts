// asistido por SI: Claude Code (Anthropic), E2E de P-C: la ayuda explica qué cambia entre Farmer y Technical, en inglés y en español
import { expect, test } from '@playwright/test'
import { ES, medirContraste } from './marco_ayuda'

test.describe('ayuda con el modo de lectura (P-C)', () => {
  test('en inglés dice qué agrega Technical y que los datos son los mismos', async ({ page }) => {
    await page.goto('/')
    await page.locator('.ayuda-boton').click()
    const ayuda = page.getByRole('dialog')
    await expect(ayuda.getByRole('heading', { name: 'Farmer and Technical' })).toBeVisible()
    await expect(ayuda).toContainText('The data are the same in both modes.')
    await expect(ayuda).toContainText('averaging over cropland or over total area')
    // El texto nuevo se lee: contraste AA sobre el fondo real del panel
    const medidas = await medirContraste(page, ['.cabecera-hoja .ayuda .modo-ayuda h3', '.cabecera-hoja .ayuda .modo-ayuda p'])
    expect(medidas.length).toBe(2)
    for (const m of medidas) expect(m.contraste, m.texto).toBeGreaterThanOrEqual(m.minimo)
  })
  test.describe('en español', () => {
    test.use({ storageState: ES })
    test('dice lo mismo con sus palabras, sin restos en inglés', async ({ page }) => {
      await page.goto('/')
      await page.locator('.ayuda-boton').click()
      const ayuda = page.getByRole('dialog')
      await expect(ayuda.getByRole('heading', { name: 'Agricultor y Técnico' })).toBeVisible()
      await expect(ayuda).toContainText('Los datos no cambian de un modo a otro.')
      await expect(ayuda.locator('.modo-ayuda')).not.toContainText(/Farmer|Technical|cropland|trade-off/)
    })
  })
})
