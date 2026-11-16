// asistido por SI: Claude Code (Anthropic), la entrada se adapta a la pantalla y al zoom sin solapes (director 20:12-20:15)
import { expect, test } from '@playwright/test'

// Ventana CSS que resulta de pantallas reales y del zoom del navegador (1920×860 al 125 % y al 200 %)
const CASOS = [{ width: 1920, height: 860 }, { width: 1536, height: 730 }, { width: 1366, height: 650 }, { width: 1280, height: 680 }, { width: 1536, height: 688 }, { width: 960, height: 430 }, { width: 390, height: 844 }]

for (const vp of CASOS) {
  test(`entrada a ${vp.width}×${vp.height}: sin solapes entre nodos ni con el título, sin desborde y con Start legible`, async ({ page }) => {
    await page.setViewportSize(vp)
    await page.goto('/#/')
    await expect(page.locator('.portada .nodo')).toHaveCount(6, { timeout: 20_000 })
    await page.waitForTimeout(800)
    const r = await page.evaluate(() => {
      const caja = (e: Element) => e.getBoundingClientRect()
      const cruza = (a: DOMRect, b: DOMRect) => !(a.right <= b.left + 0.5 || a.left >= b.right - 0.5 || a.bottom <= b.top + 0.5 || a.top >= b.bottom - 0.5)
      const titulo = caja(document.querySelector('.titulo-marca')!)
      const nodos = [...document.querySelectorAll('.portada .nodo')].map((n) => ({ id: (n as HTMLElement).dataset.nodo, r: caja(n) }))
      const solapes: string[] = []
      const frase = [...document.querySelectorAll('.portada .p-centro p')].map(caja)
      for (const n of nodos) { if (cruza(n.r, titulo)) solapes.push(`${n.id}×título`); if (frase.some((f) => cruza(n.r, f))) solapes.push(`${n.id}×frase`) }
      for (let i = 0; i < nodos.length; i++) for (let j = i + 1; j < nodos.length; j++) if (cruza(nodos[i].r, nodos[j].r)) solapes.push(`${nodos[i].id}×${nodos[j].id}`)
      const m = document.querySelector('main.portada')!
      return { solapes, desborde: m.scrollWidth - m.clientWidth }
    })
    expect(r.solapes).toEqual([])
    expect(r.desborde).toBeLessThanOrEqual(0)
    // Start se puede ver entero (con scroll si la entrada va en columna)
    const start = page.locator('.portada .comenzar')
    await start.scrollIntoViewIfNeeded()
    await expect(start).toBeInViewport({ ratio: 1 })
  })
}
