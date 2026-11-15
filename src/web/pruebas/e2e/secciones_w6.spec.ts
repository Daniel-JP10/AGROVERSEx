// asistido por SI: Claude Code (Anthropic), e2e de El gemelo del lote, Ciencia y validación y Datos abiertos (T-W6)
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

// Capturas de T-W6 en el árbol principal del repositorio (sale del worktree)
const CAPTURAS = resolve(process.cwd(), '../../../AGROVERSExz/repo/Docu/web/capturas/T-W6')
// Con VITE_EJEMPLOS=1 el servidor de desarrollo carga el ejemplo ficticio del gemelo
const CON_EJEMPLO = process.env.VITE_EJEMPLOS === '1'

// Pantalla alta para que la captura recoja toda la sección, que se desplaza por dentro
test.use({ viewport: { width: 1400, height: 1700 } })

test.describe('sin ejemplo', () => {
  test.skip(CON_EJEMPLO, 'solo sin VITE_EJEMPLOS')
  test('gemelo: sin datos dice que no hay dato y enlaza a rotaciones con el lote', async ({ page }) => {
    await page.goto('/#/gemelo?lote=DEMO-COL-01')
    await expect(page.getByRole('status')).toHaveText('Dato todavía no disponible.')
    await expect(page.locator('main svg')).toHaveCount(0)
    await page.getByRole('link', { name: 'Comparar rotaciones de este lote' }).click()
    await expect(page).toHaveURL(/#\/rotaciones\?lote=DEMO-COL-01$/)
    await page.screenshot({ path: `${CAPTURAS}/gemelo_sin_dato.png` })
  })
})

test.describe('con ejemplo', () => {
  test.skip(!CON_EJEMPLO, 'solo con VITE_EJEMPLOS=1')
  test('gemelo: cinco variables con banda, ventanas de suelo desnudo y SIMULADO', async ({ page }) => {
    await page.goto('/#/gemelo?lote=DEMO-COL-01')
    await expect(page.locator('main svg[role="img"]')).toHaveCount(5)
    await expect(page.locator('[data-rotulo="ejemplo"]')).toContainText('SIMULADO')
    await expect(page.locator('[data-valor]')).toHaveCount(10)
    await expect(page.locator('[data-ventana="firme"]').first()).toBeVisible()
    await page.screenshot({ path: `${CAPTURAS}/gemelo.png`, fullPage: true })
  })
  test('gemelo: el modo técnico y el inglés cambian los textos', async ({ page }) => {
    await page.goto('/#/gemelo')
    await page.getByRole('button', { name: 'Ayuda y glosario' }).click()
    await page.getByLabel('Técnico').check()
    await expect(page.getByText('Agua almacenada en el perfil del suelo')).toBeVisible()
    await page.getByRole('button', { name: /Idioma/ }).click()
    await expect(page.getByText('Water stored in the soil profile')).toBeVisible()
    await page.screenshot({ path: `${CAPTURAS}/gemelo_tecnico_en.png`, fullPage: true })
  })
})

test('ciencia: métricas sin dato, preguntas abiertas, limitaciones y satélite contra tierra', async ({ page }) => {
  await page.goto('/#/ciencia')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Ciencia y validación')
  await expect(page.locator('[data-metrica]')).toHaveCount(3)
  for (const m of await page.locator('[data-metrica]').all()) {
    for (const c of ['valor', 'intervalo', 'linea_base', 'n']) await expect(m.locator(`[data-campo="${c}"]`)).toContainText('Dato todavía no disponible.')
  }
  await expect(page.locator('[data-pregunta]')).toHaveCount(4)
  await expect(page.locator('[data-estado]').first()).toHaveText('abierta')
  await expect(page.locator('[data-limitacion]').first()).toBeVisible()
  await expect(page.getByText('Un satélite ve un área grande')).toBeVisible()
  await page.screenshot({ path: `${CAPTURAS}/ciencia.png`, fullPage: true })
})

test('datos abiertos: campos sin dato, sin descarga ni comando falsos', async ({ page }) => {
  await page.goto('/#/datos')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Datos abiertos')
  await expect(page.locator('[data-campo]')).toHaveCount(7)
  await expect(page.locator('main a, main code')).toHaveCount(0)
  await page.screenshot({ path: `${CAPTURAS}/datos.png`, fullPage: true })
})
