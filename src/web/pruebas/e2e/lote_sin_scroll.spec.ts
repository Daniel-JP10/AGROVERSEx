// asistido por SI: Claude Code (Anthropic), #/lote sin scroll de página ni desborde y con las 4 cifras del bloque enteras (director 17:38 y 17:44)
import { expect, test } from '@playwright/test'

const TAMANOS = [{ width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 1366, height: 768 }, { width: 1920, height: 1080 }, { width: 390, height: 844 }]

for (const vp of TAMANOS) {
  test(`#/lote a ${vp.width}×${vp.height}: sin desborde, cifras del bloque enteras y en PC sin scroll de página`, async ({ page }) => {
    await page.setViewportSize(vp)
    await page.goto('/#/lote?lote=DEMO-COL-01')
    await expect(page.locator('.bloque .l-etiqueta')).toHaveCount(4, { timeout: 30_000 })
    await page.waitForTimeout(1500)
    const r = await page.evaluate(() => {
      const m = document.querySelector('main')!, col = document.querySelector('.l-centro')!.getBoundingClientRect()
      const etiquetas = [...document.querySelectorAll('.bloque .l-etiqueta')].map((e) => { const b = e.getBoundingClientRect(); return b.top >= col.top - 1 && b.bottom <= col.bottom + 1 && b.left >= col.left - 1 && b.right <= col.right + 1 })
      const est = document.querySelector('.estrategias')!.getBoundingClientRect()
      return { desborde: m.scrollWidth - m.clientWidth, scroll: m.scrollHeight - m.clientHeight, etiquetas, estrategiasArriba: est.top < innerHeight }
    })
    expect(r.desborde, 'desborde horizontal').toBeLessThanOrEqual(0)
    expect(r.etiquetas, 'cada cifra del bloque entera').toEqual([true, true, true, true])
    if (vp.width >= 1100) {
      expect(r.scroll, 'scroll de página en PC').toBeLessThanOrEqual(0)
      expect(r.estrategiasArriba, 'las estrategias empiezan dentro de la pantalla').toBe(true)
    }
  })
}
