// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'

// Corre con AGROVERSEX_SQLITE y AGROVERSEX_DATOS definidos
test('filtro por clima: las unidades filtradas se apagan sin volverse hueco', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Filtros' }).click()
  const koppen = page.getByRole('group', { name: /Köppen/ }).getByRole('checkbox').first()
  await expect(koppen).toBeVisible({ timeout: 15000 })
  await page.evaluate(() => (window as any).__mapa.jumpTo({ center: [-60, -5], zoom: 3 }))
  await page.waitForTimeout(4000)
  await koppen.check()
  await page.waitForTimeout(3000)
  const r = await page.evaluate(() => {
    const m = (window as any).__mapa, c = m.getContainer()
    const fs = m.queryRenderedFeatures([[0, 0], [c.clientWidth, c.clientHeight]], { layers: ['adm1-relleno'] })
    const e = fs.map((f: any) => m.getFeatureState({ source: 'adm1', sourceLayer: 'adm1', id: f.properties.id }))
    return { apagadas: e.filter((x: any) => x.ok === false && x.hueco === false).length, visibles: e.filter((x: any) => x.ok === true).length }
  })
  expect(r.apagadas).toBeGreaterThan(0)
  await page.screenshot({ path: 'capturas/14-filtros.png' })
})
