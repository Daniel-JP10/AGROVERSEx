// asistido por SI: Claude Code (Anthropic), E2E de H-F3-9: en la comparación de escenarios cada cifra con su rango queda en una línea, dentro de su celda
import { expect, test } from '@playwright/test'

for (const [w, h] of [[1920, 1080], [1440, 900], [1280, 680], [390, 844], [360, 640]]) {
  test(`cifra entera en Scenario comparison a ${w}×${h}`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: h })
    await page.goto('/#/rotaciones?lote=DEMO-COL-01')
    await expect(page.getByTestId('fila-escenario')).toHaveCount(4)
    const r = await page.evaluate(() => {
      const bs = [...document.querySelectorAll<HTMLElement>('.comparador-esc .banda')]
      // Líneas que ocupa la cifra sin la unidad, medidas con un Range sobre el texto
      const lineas = (e: HTMLElement) => {
        const tn = e.firstChild!, i = tn.textContent!.lastIndexOf(')') + 1, rg = document.createRange()
        rg.setStart(tn, 0); rg.setEnd(tn, i)
        return new Set([...rg.getClientRects()].filter((q) => q.width > 0).map((q) => Math.round(q.top))).size
      }
      const t = document.querySelector('.comparador-esc table')!, s = document.querySelector('.comparador-esc')!
      return {
        pastillas: bs.length,
        partidas: bs.filter((e) => lineas(e) > 1).map((e) => e.textContent),
        fuera_celda: bs.filter((e) => e.getBoundingClientRect().right > e.closest('td')!.getBoundingClientRect().right + 0.5).length,
        tabla_fuera: t.getBoundingClientRect().right - (s.getBoundingClientRect().right - parseFloat(getComputedStyle(s).paddingRight)),
        nombres_cortados: [...document.querySelectorAll('.comparador-esc th')].filter((e) => e.scrollWidth > e.clientWidth + 1).length,
        desborde_doc: document.documentElement.scrollWidth - innerWidth,
      }
    })
    expect(r.pastillas).toBe(8)
    expect(r.partidas).toEqual([])
    expect(r.fuera_celda).toBe(0)
    expect(r.tabla_fuera).toBeLessThanOrEqual(0.5)
    expect(r.nombres_cortados).toBe(0)
    expect(r.desborde_doc).toBe(0)
  })
}
