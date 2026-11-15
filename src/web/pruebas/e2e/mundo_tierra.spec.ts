// asistido por SI: Claude Code (Anthropic), E2E de las series del mundo en el build desplegado: relleno fuera de COL en 3 niveles, ponderación y PI-D1 (S1w)
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { gunzipSync } from 'node:zlib'
import { expect, test, type Page } from '@playwright/test'

const DIST = join(process.cwd(), 'dist')
const PAIS = 'KEN'
const IDIOMAS = [
  { idioma: 'en', tecnico: 'Technical', area: 'Total area mean', pid1: /Between \d+\.\d and \d+\.\d % of unit-month pairs change with the definition \(PI-D1\)/ },
  { idioma: 'es', tecnico: 'Técnico', area: 'Media sobre el área total', pid1: /Entre \d+,\d y \d+,\d % de los pares unidad-mes cambian con la definición \(PI-D1\)/ },
] as const
const conIdioma = (page: Page, idioma: string) => page.addInitScript((i) => { try { localStorage.setItem('agroversex-idioma', i) } catch { /* sin almacenamiento */ } }, idioma)
const meta = () => JSON.parse(readFileSync(join(DIST, 'datos/meta.json'), 'utf-8'))
const ids = (ruta: string): string[] => JSON.parse(gunzipSync(readFileSync(join(DIST, 'datos', ruta))).toString('utf-8')).ids

// Cuántas unidades del país llevan valor pintado en el estado de la fuente del nivel
async function pintadas(page: Page, nivel: number): Promise<number> {
  return page.evaluate(([n, p]) => {
    const m = (window as any).__mapa
    const fs = m.querySourceFeatures(`adm${n}`, { sourceLayer: `adm${n}` })
    return fs.filter((f: any) => String(f.properties?.unidad_id ?? '').startsWith(`${p}-`) && m.getFeatureState({ source: `adm${n}`, sourceLayer: `adm${n}`, id: f.id }).ok === true).length
  }, [nivel, PAIS] as const)
}
// Valor del estado de una unidad
const valor = (page: Page, nivel: number, id: string) => page.evaluate(([n, i]) => (window as any).__mapa.getFeatureState({ source: `adm${n}`, sourceLayer: `adm${n}`, id: i }).v, [nivel, id] as const)

test('meta.json del despliegue trae el mundo y los productos en inglés', () => {
  const m = meta()
  expect(m.paises.length).toBeGreaterThan(100)
  expect(m.paises).toContain(PAIS)
  expect(m.paises_adm2).toContain(PAIS)
  expect(m.ponderacion_defecto).toBe('cultivo')
  for (const v of Object.values(m.variables) as { productos: { producto: string }[] }[]) for (const p of v.productos) expect(p.producto).not.toMatch(/mensual|diario|grados|reanálisis/)
})

for (const L of IDIOMAS) {
  test.describe(`idioma ${L.idioma}`, () => {
    test.beforeEach(async ({ page }) => conIdioma(page, L.idioma))

    test(`${PAIS}: relleno en los 3 niveles y la ponderación cambia el relleno`, async ({ page }) => {
      test.setTimeout(150_000)
      const adm1 = ids('MUNDO/precip_1_cultivo.json.gz').find((x) => x.startsWith(`${PAIS}-`))!
      await page.goto('/#/tierra')
      await page.waitForFunction(() => !!(window as any).__mapa?.isStyleLoaded())
      // Centro de Kenia a tres zooms: país, adm1 y adm2
      for (const [nivel, zoom] of [[0, 3], [1, 5.5], [2, 7.5]] as const) {
        await page.evaluate((z) => (window as any).__mapa.jumpTo({ center: [37.9, 0.2], zoom: z }), zoom)
        await expect.poll(() => pintadas(page, nivel), { timeout: 60_000, message: `nivel ${nivel}` }).toBeGreaterThan(0)
      }
      await page.evaluate(() => (window as any).__mapa.jumpTo({ center: [37.9, 0.2], zoom: 5.5 }))
      await expect.poll(() => pintadas(page, 1), { timeout: 60_000 }).toBeGreaterThan(0)
      const antes = await valor(page, 1, adm1)
      // Technical: aparece la elección y la línea PI-D1
      await page.getByRole('button', { name: L.tecnico, exact: true }).click()
      const ley = page.getByRole('group', { name: /legend|leyenda/i })
      await expect(ley.locator('p.pid1')).toHaveText(new RegExp(L.pid1.source))
      await ley.getByRole('radio', { name: L.area }).check()
      await expect.poll(() => valor(page, 1, adm1), { timeout: 60_000 }).not.toBe(antes)
      await expect(ley.locator('[data-ponderacion]')).toHaveAttribute('data-ponderacion', 'area')
    })
  })
}

// Capturas del encargo (MUNDO_CAPTURAS=1, solo chromium): Kenia en Technical, 1440 x 900 y 390 x 844, en inglés
const VERIF = process.env.MUNDO_CAPTURAS
test.describe('capturas', () => {
  test.skip(!VERIF, 'solo con MUNDO_CAPTURAS=<carpeta>')
  for (const [ancho, alto] of [[1440, 900], [390, 844]] as const) {
    test(`captura ${ancho}`, async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium')
      await page.setViewportSize({ width: ancho, height: alto })
      await conIdioma(page, 'en')
      await page.goto('/#/tierra')
      await page.waitForFunction(() => !!(window as any).__mapa?.isStyleLoaded())
      await page.evaluate(() => (window as any).__mapa.jumpTo({ center: [37.9, 0.2], zoom: 5.5 }))
      await expect.poll(() => pintadas(page, 1), { timeout: 60_000 }).toBeGreaterThan(0)
      await page.getByRole('button', { name: 'Technical', exact: true }).click()
      await page.waitForTimeout(1500)
      await page.screenshot({ path: join(VERIF!, `f3_S1w_tierra_${ancho}.png`) })
      // contraste AA de los textos nuevos de la leyenda sobre su fondo real
      const c = await page.evaluate(() => {
        const rgb = (s: string) => (s.match(/[\d.]+/g) ?? []).map(Number)
        const lum = ([r, g, b]: number[]) => { const f = (x: number) => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4 }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b) }
        const fondo = (el: Element | null): number[] => { while (el) { const b = rgb(getComputedStyle(el).backgroundColor); if (b.length >= 3 && (b[3] ?? 1) > 0.9) return b; el = el.parentElement } return [0, 0, 0] }
        return [...document.querySelectorAll('.leyenda p.pid1, .leyenda p.limites, .leyenda .ponderacion label, .leyenda [data-ponderacion]')].map((e) => {
          const a = lum(rgb(getComputedStyle(e).color)), b = lum(fondo(e))
          return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
        })
      })
      console.log(`contraste ${ancho}: ${c.map((x) => x.toFixed(2)).join(', ')}`)
      for (const x of c) expect(x).toBeGreaterThanOrEqual(4.5)
    })
  }
})
