// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { expect, test } from '@playwright/test'

// Se ejecuta con playwright.e2e.config.ts (Chrome real)
test('línea de tiempo: teclado, sin dato antes de SMAP, reproducción sin errores', async ({ page }) => {
  const errores: string[] = []
  page.on('pageerror', (e) => e.message !== 'Failed to fetch' && errores.push(e.message)) // fetch del globo (Task 6), ajeno
  page.on('console', (m) => m.type() === 'error' && !/api\/|favicon|Failed to (load resource|fetch)/.test(m.text()) && errores.push(m.text()))
  await page.goto('/#/tierra')
  const mes = page.getByTestId('mes')
  await page.getByLabel('Mes', { exact: true }).focus()
  await page.keyboard.press('Home')
  await expect(mes).toHaveText('ene-2000')
  await page.keyboard.press('Shift+ArrowRight')
  await expect(mes).toHaveText('ene-2001')
  await page.getByLabel('Mes', { exact: true }).fill('181') // feb-2015
  await expect(mes).toHaveText('feb-2015')
  await expect(page.getByTestId('nota')).toContainText('sin dato · SMAP L3')
  await page.getByLabel('Mes', { exact: true }).focus()
  await page.keyboard.press('Space')
  await page.waitForTimeout(3000)
  await page.screenshot({ path: 'capturas/tiempo.png' })
  await page.keyboard.press('Space')
  await expect(mes).not.toHaveText('feb-2015')
  expect(errores).toEqual([])
})
