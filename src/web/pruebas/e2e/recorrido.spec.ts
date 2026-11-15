// asistido por SI: Claude Code (Anthropic), e2e de la portada, el recorrido completo con teclado y la sección Fuentes
import { resolve } from 'node:path'
import { expect, test, type Page } from '@playwright/test'

// Capturas de T-W1 y T-W3 en el árbol principal del repositorio (sale del worktree)
const CAPTURAS = resolve(process.cwd(), '../../../AGROVERSExz/repo/Docu/web/capturas/T-W1_T-W3')
// Ruta de cada uno de los dieciséis pasos del guion
const RUTAS = ['', 'tierra', 'ciencia', 'ciencia', 'tierra', 'tierra', 'tierra', 'tierra', 'tierra', 'rotaciones', 'rotaciones', 'rotaciones', 'rotaciones', 'rotaciones', 'datos', 'fuentes']
// Pasos que se capturan: portada, algunos pasos intermedios y el cierre
const CAPTURA_PASO: Record<number, string> = { 0: 'portada-paso-1-1', 2: 'paso-1-3', 4: 'paso-2-1', 12: 'paso-3-5', 15: 'cierre-paso-4-2' }

const hash = (page: Page) => new URL(page.url()).hash.replace(/^#\//, '').split('?')[0]
const enPanel = (page: Page) => page.locator('section.recorrido')
const siguiente = (page: Page) => enPanel(page).getByRole('button', { name: 'Siguiente' })

async function enfocarInicio(page: Page) {
  const inicio = page.getByRole('button', { name: 'Iniciar el recorrido guiado' })
  for (let i = 0; i < 30 && !(await inicio.evaluate((e) => e === document.activeElement)); i++) await page.keyboard.press('Tab')
  await expect(inicio).toBeFocused()
  return inicio
}

test('portada: idea en dos frases y botón de inicio, sin aviso de dato pendiente', async ({ page }) => {
  await page.goto('/#/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('AGROVERSEx')
  await expect(page.locator('main.portada p')).toHaveCount(2)
  await expect(page.getByRole('button', { name: 'Iniciar el recorrido guiado' })).toBeVisible()
  await expect(page.locator('section.recorrido')).toHaveCount(0)
  await page.screenshot({ path: `${CAPTURAS}/portada.png` })
})

test('recorrido completo solo con teclado: los dieciséis pasos, atrás con Mayús+Tab, salir y devolver el foco', async ({ page }) => {
  test.setTimeout(180_000)
  await page.goto('/#/')
  const inicio = await enfocarInicio(page)
  await page.keyboard.press('Enter')
  const panel = page.locator('section.recorrido')
  await expect(panel).toBeVisible()
  await expect(siguiente(page)).toBeFocused()

  for (let i = 0; i < RUTAS.length; i++) {
    await expect.poll(() => hash(page), { message: `ruta del paso ${i + 1}` }).toBe(RUTAS[i])
    const texto = page.getByTestId('paso-texto')
    await expect(texto).not.toBeEmpty()
    expect(await texto.innerText(), `paso ${i + 1}`).not.toMatch(/\d/)
    await expect(panel.locator('[aria-live="polite"]')).toHaveCount(1)
    if (i in CAPTURA_PASO) { await page.waitForTimeout(i === 4 ? 2500 : 300); await page.screenshot({ path: `${CAPTURAS}/${CAPTURA_PASO[i]}.png` }) }
    if (i === 2) {
      // Atrás con teclado: Mayús+Tab llega a Anterior y Enter vuelve al paso previo; el foco no se pierde
      await page.keyboard.press('Shift+Tab')
      await expect(enPanel(page).getByRole('button', { name: 'Anterior' })).toBeFocused()
      await page.keyboard.press('Enter')
      await expect.poll(() => hash(page)).toBe(RUTAS[1])
      await page.keyboard.press('Tab')
      await expect(siguiente(page)).toBeFocused()
      await page.keyboard.press('Enter')
      await expect.poll(() => hash(page)).toBe(RUTAS[2])
    }
    if (i < RUTAS.length - 1) {
      await expect(siguiente(page)).toBeFocused()
      await page.keyboard.press('Enter')
    }
  }

  // Último paso: el botón pasa a Terminar y cierra el recorrido
  const terminar = enPanel(page).getByRole('button', { name: 'Terminar' })
  await expect(terminar).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(panel).toHaveCount(0)
  expect(hash(page)).toBe('fuentes')
  void inicio
})

test('Escape cierra el recorrido y el foco vuelve al botón de la portada', async ({ page }) => {
  await page.goto('/#/')
  const inicio = await enfocarInicio(page)
  await page.keyboard.press('Enter')
  await expect(page.locator('section.recorrido')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('section.recorrido')).toHaveCount(0)
  await expect(inicio).toBeFocused()
})

test('el recorrido sin datos muestra el aviso de dato no disponible en el paso que lo necesita', async ({ page }) => {
  await page.goto('/#/')
  await page.getByRole('button', { name: 'Iniciar el recorrido guiado' }).click()
  await expect(page.getByTestId('paso-texto')).not.toContainText('Dato todavía no disponible.')
  await siguiente(page).click()
  await expect(page.getByTestId('paso-texto')).toContainText('Dato todavía no disponible.')
})

test('movimiento reducido: el panel no usa animaciones ni transiciones', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/#/')
  await page.getByRole('button', { name: 'Iniciar el recorrido guiado' }).click()
  const estilo = await page.locator('section.recorrido').evaluate((e) => { const c = getComputedStyle(e); return [c.animationName, c.transitionDuration] })
  expect(estilo[0]).toBe('none')
  expect(estilo[1]).toMatch(/^0s(, 0s)*$/)
})

test('Fuentes: glosario, créditos y declaración de SI; el modo cambia el texto y no los números', async ({ page }) => {
  await page.goto('/#/fuentes')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Fuentes, glosario y créditos')
  await expect(page.locator('dl.glosario dt')).toHaveCount(8)
  await expect(page.locator('table[data-tabla] tbody tr')).not.toHaveCount(0)
  await expect(page.getByTestId('declaracion-si')).toContainText('Claude Code (Anthropic)')
  const glosario = page.locator('dl.glosario')
  const numeros = async () => ((await glosario.innerText()).match(/(?<![\w-])\d+(?:[.,]\d+)?(?![\w-])/g) ?? [])
  const agricultor = await glosario.innerText()
  const numerosAgricultor = await numeros()
  await page.screenshot({ path: `${CAPTURAS}/fuentes-agricultor.png` })
  const creditos = () => page.locator('table[data-tabla]').evaluateAll((ts) => ts.map((t) => (t as HTMLElement).innerText).join('\n'))
  const creditosAntes = await creditos()
  expect(agricultor).not.toContain('Dato todavía no disponible.')
  await page.getByRole('radio', { name: 'Técnico' }).check()
  const tecnico = await glosario.innerText()
  expect(tecnico.length).toBeGreaterThan(agricultor.length)
  expect(tecnico).toContain('Dato todavía no disponible.')
  expect(await numeros()).toEqual(numerosAgricultor)
  expect(await creditos()).toBe(creditosAntes)
  await page.screenshot({ path: `${CAPTURAS}/fuentes-tecnico.png` })
  await page.locator('details[data-credito]').first().scrollIntoViewIfNeeded()
  await page.locator('#creditos').scrollIntoViewIfNeeded()
  await page.screenshot({ path: `${CAPTURAS}/fuentes-creditos.png` })
})
