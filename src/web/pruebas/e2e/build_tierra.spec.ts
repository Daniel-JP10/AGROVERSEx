// asistido por SI: Claude Code (Anthropic), E2E del globo en el build estático: búsqueda, unidad por ruta y cero llamadas a /api/ (D-037 C2)
import { expect, test, type Page } from '@playwright/test'

const IPIALES = 'COL-ADM2-7082276B52108893597118'
const SIN_BASE = /sin base de datos|no database/i

// Toda petición del navegador queda anotada; ninguna puede ser a /api/
function espiarApi(page: Page): string[] {
  const api: string[] = []
  page.on('request', (r) => { if (new URL(r.url()).pathname.startsWith('/api/')) api.push(r.url()) })
  return api
}

test('buscar Ipiales, elegirla, cambiar variable y mes: panel con valores y sin /api/', async ({ page }) => {
  const api = espiarApi(page)
  await page.goto('/#/tierra')
  const campo = page.getByRole('combobox', { name: /buscar|search/i })
  await expect(campo).toHaveAttribute('placeholder', /buscar|search/i, { timeout: 60_000 })
  await campo.fill('Ipiales')
  const opcion = page.getByRole('option').filter({ hasText: /Nariño/ }).first()
  await opcion.click()
  const panel = page.getByRole('complementary', { name: /panel de región|region panel/i })
  await expect(panel).toBeVisible()
  await expect(page.getByRole('navigation', { name: /ubicación|location/i })).toContainText('Ipiales')
  await expect(page.getByText(SIN_BASE)).toHaveCount(0)
  // el panel trae un valor numérico del archivo estático
  await expect(panel).toContainText(/\d/, { timeout: 30_000 })
  const antes = await panel.innerText()
  // variable por el panel de capas y mes por el control de la línea de tiempo
  await page.getByRole('button', { name: /^(capas|layers)/i }).click()
  await page.getByRole('radio', { name: /temperatura|temperature/i }).check()
  await expect(page.getByRole('combobox', { name: /producto|product/i })).toHaveValue('merra2')
  const mes0 = await page.getByTestId('mes').innerText()
  await page.getByRole("slider", { name: /mes|month/i }).focus()
  await page.keyboard.press('Shift+ArrowRight') // +12 meses
  await expect(page.getByTestId('mes')).not.toHaveText(mes0)
  await expect.poll(async () => panel.innerText()).not.toBe(antes)
  expect(api, `llamadas a /api/: ${api.join(', ')}`).toEqual([])
})

test(`la ruta con unidad, variable y mes aplica los tres`, async ({ page }) => {
  const api = espiarApi(page)
  await page.goto(`/#/tierra?unidad=${IPIALES}&variable=t2m&mes=2015-01`)
  const panel = page.getByRole('complementary', { name: /panel de región|region panel/i })
  await expect(panel).toBeVisible({ timeout: 60_000 })
  await expect(page.getByRole('navigation', { name: /ubicación|location/i })).toContainText('Ipiales')
  await expect(page.getByTestId('mes')).toContainText(/ene-2015|jan-2015/i)
  await expect(page.getByRole('combobox', { name: /producto|product/i })).toHaveValue('merra2') // t2m
  await expect(panel).toContainText(/\d+[.,]\d/, { timeout: 30_000 }) // valor con decimales del archivo estático
  await expect(page.getByText(SIN_BASE)).toHaveCount(0)
  // cambiar el hash con la app abierta vuelve a aplicar los parámetros
  await page.evaluate(() => { window.location.hash = '#/tierra?variable=ndvi&mes=2020-06' })
  await expect(page.getByTestId('mes')).toContainText(/jun-2020/i)
  await expect(page.getByRole('combobox', { name: /producto|product/i })).toHaveValue('mod13') // ndvi
  expect(api, `llamadas a /api/: ${api.join(', ')}`).toEqual([])
})

test('recorrer pestañas del panel y herramientas del riel no llama a /api/', async ({ page }) => {
  const api = espiarApi(page)
  await page.goto(`/#/tierra?unidad=${IPIALES}`)
  const panel = page.getByRole('complementary', { name: /panel de región|region panel/i })
  await expect(panel).toBeVisible({ timeout: 60_000 })
  // corre en inglés (idioma por defecto): las pestañas se buscan por su etiqueta inglesa (C-1)
  for (const pestana of ['Time series', 'Soil', 'Rotations', 'Sources', 'Summary']) {
    await panel.getByRole('tab', { name: pestana }).click()
    await expect(panel.getByRole('tab', { name: pestana })).toHaveAttribute('aria-selected', 'true')
    await page.waitForTimeout(400) // deja salir las peticiones de la pestaña
  }
  const riel = page.getByRole('navigation', { name: /herramientas|tools/i })
  for (const boton of await riel.getByRole('button').all()) { await boton.click(); await page.waitForTimeout(400) }
  expect(api, `llamadas a /api/: ${api.join(', ')}`).toEqual([])
})
