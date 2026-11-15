// asistido por SI: Claude Code (Anthropic), e2e de #/rotaciones con y sin lote; el ejemplo solo con VITE_EJEMPLOS=1
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const CAPTURAS = resolve(process.cwd(), '../../../AGROVERSExz/repo/Docu/web/capturas/T-W2')
const CON_EJEMPLO = process.env.VITE_EJEMPLOS === '1'

test('sin lote explica que no hay lote DEMO y no muestra resultados', async ({ page }) => {
  await page.goto('/#/rotaciones')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Rotaciones')
  await expect(page.getByText('No hay un lote DEMO elegido')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Ir a La Tierra desde el espacio' })).toBeVisible()
  await expect(page.getByTestId('estrategia')).toHaveCount(0)
  await expect(page.locator('[data-banda]')).toHaveCount(0)
  await page.screenshot({ path: resolve(CAPTURAS, 'rotaciones_sin_lote.png'), fullPage: true })
})

test('con lote pero sin la bandera de ejemplos no inventa resultados', async ({ page }) => {
  test.skip(CON_EJEMPLO, 'solo sin VITE_EJEMPLOS')
  await page.goto('/#/rotaciones?lote=DEMO-USA-01')
  await expect(page.getByRole('status')).toHaveText('Dato todavía no disponible.')
  await expect(page.getByTestId('estrategia')).toHaveCount(0)
})

test('con lote y el ejemplo: línea base, tres alternativas, Pareto y partes pendientes', async ({ page }) => {
  test.skip(!CON_EJEMPLO, 'requiere VITE_EJEMPLOS=1')
  await page.goto('/#/rotaciones?unidad=USA-ADM2-EJEMPLO&lote=DEMO-USA-01')
  await expect(page.getByTestId('rotulo')).toHaveText('SIMULADO')
  await expect(page.getByTestId('aviso-gemelo')).toBeVisible()
  await expect(page.getByTestId('linea-base')).toHaveCount(1)
  expect(await page.getByTestId('estrategia').count()).toBeGreaterThanOrEqual(4)
  for (const b of ['porque', 'evidencia', 'beneficios', 'vacios', 'riesgos']) await expect(page.locator(`[data-bloque=${b}]`).first()).toBeVisible()
  const pareto = page.getByTestId('pareto')
  await expect(pareto.locator('svg')).toBeVisible()
  await expect(pareto).toContainText('Rotación actual (línea base)')
  const antes = await pareto.locator('svg').innerHTML()
  await page.getByLabel('Eje vertical').selectOption({ index: 3 })
  await expect.poll(async () => pareto.locator('svg').innerHTML()).not.toBe(antes)
  await expect(page.getByRole('heading', { name: 'Compromisos frente a la rotación actual' })).toBeVisible()
  for (const h of ['Tus prioridades', 'Escenarios de lluvia y temperatura', 'Alertas del lote', 'Calibra con los datos de tu lote']) await expect(page.getByRole('heading', { name: h })).toBeVisible()
  await page.screenshot({ path: resolve(CAPTURAS, 'rotaciones_con_lote.png'), fullPage: true })
  await pareto.scrollIntoViewIfNeeded()
  await pareto.screenshot({ path: resolve(CAPTURAS, 'rotaciones_pareto.png') })
})
