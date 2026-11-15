// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'
import { ES } from './idioma'

test.use({ storageState: ES }) // asserta español y el idioma por defecto es el inglés (D-039)

// Corre con AGROVERSEX_SQLITE (base) y AGROVERSEX_DATOS (teselas e índice) definidos
test('coropleta con datos reales: leyenda, etiqueta central y opacidad', async ({ page }) => {
  await page.goto('/#/tierra')
  await expect(page.locator('.leyenda')).toContainText('GPM IMERG')
  await page.waitForTimeout(3000)
  await page.evaluate(() => (window as any).__mapa.jumpTo({ center: [-74.07, 4.65], zoom: 10 }))
  await page.waitForTimeout(5000)
  await expect(page.locator('.etiqueta-centro')).toContainText('mm/mes')
  const estado = await page.evaluate(() => {
    const m = (window as any).__mapa, c = m.getContainer()
    const f = m.queryRenderedFeatures([c.clientWidth / 2, c.clientHeight / 2], { layers: ['adm2-relleno'] })[0]
    return f && m.getFeatureState({ source: 'adm2', sourceLayer: 'adm2', id: f.properties.id })
  })
  expect(estado?.ok === true || estado?.hueco === true).toBe(true)
  await page.locator('.riel button').first().click()
  await page.locator('#op-coropleta').fill('90')
  expect(await page.evaluate(() => localStorage.getItem('agroversex.coropleta.opacidad'))).toBe('90')
  await page.locator('#op-coropleta').fill('62')
  await page.screenshot({ path: 'capturas/06-coropleta-z10.png' })
})
