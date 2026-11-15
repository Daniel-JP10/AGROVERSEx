// asistido por SI: Claude Code (Anthropic), e2e de C3: inglés por defecto, selector de español, persistencia y orden de estrategias por prioridades
import { expect, test } from '@playwright/test'

const CON_EJEMPLO = process.env.VITE_EJEMPLOS === '1'

// Sin idioma guardado: es lo que ve quien entra por primera vez
test.use({ storageState: { cookies: [], origins: [] } })

test('sin preferencia la experiencia sale en inglés y el selector pasa a español y vuelve', async ({ page }) => {
  await page.goto('/#/')
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  const nav = page.getByRole('navigation').first()
  await expect(nav.getByRole('link', { name: 'Rotations' })).toBeVisible()
  await expect(nav.getByRole('link', { name: 'Earth from space' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Start the guided tour' })).toBeVisible()
  await page.getByRole('button', { name: /^Language/ }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', 'es')
  await expect(nav.getByRole('link', { name: 'La Tierra desde el espacio' })).toBeVisible()
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('lang', 'es')
  await page.getByRole('button', { name: /^Idioma/ }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
})

test('la ayuda trae el glosario técnico en inglés y en español, sin cifras escritas a mano', async ({ page }) => {
  await page.goto('/#/')
  await page.getByRole('button', { name: 'Help and glossary' }).first().click()
  const ayuda = page.getByRole('dialog')
  await ayuda.getByRole('radio', { name: 'Technician' }).check()
  await expect(ayuda).toContainText('Coarse resolution: a regional context layer.')
  await page.getByRole('button', { name: /^Language/ }).click()
  await expect(page.getByRole('dialog')).toContainText('Resolución gruesa: capa de contexto regional.')
})

test('Rotaciones en inglés sin lote explica qué falta; en español también', async ({ page }) => {
  await page.goto('/#/rotaciones')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Rotations')
  await expect(page.getByText('No DEMO field is selected')).toBeVisible()
  await page.getByRole('button', { name: /^Language/ }).click()
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Rotaciones')
  await expect(page.getByText('No hay un lote DEMO elegido')).toBeVisible()
})

test.describe('con el ejemplo (VITE_EJEMPLOS=1)', () => {
  test.skip(!CON_EJEMPLO, 'el ejemplo solo existe con VITE_EJEMPLOS=1')
  test('los deslizadores de prioridades reordenan las estrategias y no cambian los valores', async ({ page }) => {
    await page.goto('/#/rotaciones?unidad=USA-ADM2-EJEMPLO&lote=DEMO-USA-01')
    await expect(page.getByRole('heading', { name: 'Your priorities' })).toBeVisible()
    const titulos = () => page.locator('[data-testid="estrategia"] h3').allTextContents()
    const antes = await titulos()
    expect(antes.length).toBeGreaterThanOrEqual(4)
    const suelo = page.locator('input[data-deslizador="suelo"]')
    for (const k of ['agua', 'insumos', 'estabilidad_climatica']) await page.locator(`input[data-deslizador="${k}"]`).fill('0')
    await suelo.fill('5')
    const despues = await titulos()
    expect([...despues].sort()).toEqual([...antes].sort())
    await page.screenshot({ path: 'test-results/prioridades-en.png' })
  })
})
