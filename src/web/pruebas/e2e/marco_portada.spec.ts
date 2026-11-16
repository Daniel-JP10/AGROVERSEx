// asistido por SI: Claude Code (Anthropic), E2E del marco común y la entrada sobre el build estático, en los tres motores
import { expect, test } from '@playwright/test'
import { ES, medirContraste, prohibidosEnTexto } from './marco_ayuda'

const NODOS_EN = ['Earth from space', "Your field's twin", 'Rotations', 'Science and validation', 'Open data', 'Sources, glossary and credits']
const NAV_EN = ['Earth', 'Your field', 'Rotations', 'Science and validation', 'Open data', 'Sources']
const RUTAS = ['', 'tierra', 'lote', 'rotaciones', 'ciencia', 'datos', 'fuentes']
const TEXTOS = ['.cabecera-hoja .marca', '.cabecera-hoja .nav a', '.cabecera-hoja .acciones button', '.pie p', '.portada h1', '.portada .p-centro p', '.portada .nodo span', '.portada .comenzar']

test.describe('entrada en inglés (sin idioma guardado)', () => {
  test('frase, seis nodos navegables en orden del reloj y Start a #/tierra', async ({ page, browserName }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('AGROVERSEx')
    await expect(page.getByText('Your land through NASA open data, from space down to your field.')).toBeVisible()
    await expect(page.getByText('Compare rotations with a digital twin that shows ranges, not promises.')).toBeVisible()
    const nodos = page.getByRole('navigation', { name: 'Explore by section' }).getByRole('link')
    await expect(nodos).toHaveText(NODOS_EN)
    // Tab recorre los nodos en el orden del reloj, con foco visible
    // Desde el último control de la cabecera, con teclado (así aplica :focus-visible)
    await page.locator('.ayuda-boton').focus()
    await page.keyboard.press('Tab')
    const leerFoco = () => page.evaluate(() => {
      const a = document.activeElement as HTMLElement
      const cs = getComputedStyle(a)
      return { nodo: a.dataset.nodo ?? '', contorno: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) >= 2 }
    })
    const orden: string[] = []
    for (let i = 0; i < 6; i++) {
      // WebKit en Windows, como Safari por defecto, no lleva el Tab a los enlaces: ahí se enfoca cada nodo tras usar el teclado
      // y el orden del reloj se comprueba por el orden del DOM (sin tabindex, es el orden de tabulación)
      if (browserName === 'webkit') await page.locator('.portada .nodo').nth(i).focus()
      const foco = await leerFoco()
      expect(foco.contorno, foco.nodo).toBe(true)
      orden.push(foco.nodo)
      if (browserName !== 'webkit') await page.keyboard.press('Tab')
    }
    expect(await page.locator('.portada [tabindex]').count()).toBe(0)
    expect(orden).toEqual(['tierra', 'lote', 'rotaciones', 'ciencia', 'datos', 'fuentes'])
    await page.getByRole('link', { name: 'Start' }).click()
    await expect(page).toHaveURL(/#\/tierra$/)
  })

  test('si la imagen de un nodo no carga, cae a su ícono SVG', async ({ page }) => {
    await page.route('**/portada/globo.webp', (r) => r.fulfill({ status: 404 }))
    await page.route('**/lotes/bloque_DEMO-COL-01.webp', (r) => r.fulfill({ status: 404 }))
    await page.goto('/')
    for (const n of ['tierra', 'lote']) {
      await expect(page.locator(`[data-nodo="${n}"] svg.icono-nodo`)).toBeVisible()
      await expect(page.locator(`[data-nodo="${n}"] img`)).toHaveCount(0)
    }
  })

  test('las raíces crecen al cargar (stroke-dashoffset animado)', async ({ page }) => {
    await page.goto('/')
    const anim = await page.locator('.raiz').first().evaluate((el) => getComputedStyle(el).animationName)
    expect(anim).toBe('raiz-crece')
    await expect.poll(() => page.locator('.raiz').first().evaluate((el) => parseFloat(getComputedStyle(el).strokeDashoffset)), { timeout: 5000 }).toBeLessThan(0.01)
  })

  test('cabecera: AGROVERSEx sin SIMULADO ni DEMO, seis secciones, selectores y sin ícono de usuario', async ({ page }) => {
    await page.goto('/#/ciencia')
    const cab = page.locator('header.cabecera-hoja')
    await expect(cab.locator('.marca')).toHaveText('AGROVERSEx')
    expect(await cab.innerText()).not.toMatch(/SIMULADO|SIMULATED|DEMO/)
    await expect(cab.getByRole('navigation').getByRole('link')).toHaveText(NAV_EN)
    await expect(cab.locator('nav a[aria-current="page"]')).toHaveText('Science and validation')
    await expect(cab.getByRole('button', { name: 'Farmer' })).toHaveAttribute('aria-pressed', 'true')
    await cab.getByRole('button', { name: 'Technical' }).click()
    await expect(cab.getByRole('button', { name: 'Technical' })).toHaveAttribute('aria-pressed', 'true')
    await expect(cab.getByRole('button', { name: /^Language/ })).toBeVisible()
    expect(await cab.locator('[aria-label*="user" i], [aria-label*="usuario" i], [class*="usuario"], [class*="user"]').count()).toBe(0)
    await expect(page.locator('footer.pie')).toContainText('Decision-support tool')
  })

  test('#/gemelo redirige a #/lote con su lote y la sección tiene respaldo', async ({ page }) => {
    await page.goto('/#/gemelo?lote=DEMO-COL-01')
    await expect(page).toHaveURL(/#\/lote\?lote=DEMO-COL-01$/)
    await expect(page.locator('.cabecera-hoja nav a[aria-current="page"]')).toHaveText('Your field')
    await expect(page.locator('main')).toBeVisible()
  })

  test('las decoraciones no se enfocan ni reciben clics', async ({ page }) => {
    await page.goto('/')
    const malas = await page.evaluate(() => Array.from(document.querySelectorAll('.decoracion, .decoracion *, .raices, .raices *, .cabecera-contorno'))
      .filter((el) => el.closest('[aria-hidden="true"]') === null || getComputedStyle(el).pointerEvents !== 'none' || el.hasAttribute('tabindex')).length)
    expect(malas).toBe(0)
  })

  test('contraste AA en la entrada y el marco, medido sobre el fondo real', async ({ page }) => {
    await page.goto('/')
    await page.waitForTimeout(1800)
    const medidas = await medirContraste(page, TEXTOS)
    expect(medidas.length).toBeGreaterThan(15)
    expect(medidas.filter((m) => m.contraste < m.minimo)).toEqual([])
  })

  test('ningún texto prohibido se ve en las siete rutas', async ({ page }) => {
    for (const r of RUTAS) {
      await page.goto(`/#/${r}`)
      await expect(page.locator('main').first()).toBeVisible()
      await page.waitForTimeout(r === 'tierra' ? 1500 : 300)
      const texto = await page.locator('body').innerText()
      expect(prohibidosEnTexto(texto), r).toEqual([])
      expect(await page.locator('header').first().innerText(), r).not.toMatch(/SIMULADO|DEMO/)
    }
  })
})

test.describe('movimiento reducido', () => {
  test.use({ reducedMotion: 'reduce' })
  test('las raíces se pintan ya crecidas, sin animación', async ({ page }) => {
    await page.goto('/')
    // Espera a que la entrada monte sus 6 raíces antes de leer su estilo (evaluar antes daba 0 raíces con la CPU cargada)
    await expect(page.locator('.raiz')).toHaveCount(6, { timeout: 20_000 })
    const raices = await page.locator('.raiz').evaluateAll((els) => els.map((el) => ({ a: getComputedStyle(el).animationName, d: parseFloat(getComputedStyle(el).strokeDashoffset) })))
    expect(raices).toHaveLength(6)
    for (const r of raices) { expect(r.a).toBe('none'); expect(r.d).toBe(0) }
  })
})

test.describe('entrada en español', () => {
  test.use({ storageState: ES })
  test('frase del director, nodos y Comenzar en español; contraste AA', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Tu tierra vista con datos abiertos de la NASA, del espacio a tu lote.')).toBeVisible()
    await expect(page.getByText('Compara rotaciones con un gemelo digital que muestra rangos, no promesas.')).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Explora por sección' }).getByRole('link')).toHaveCount(6)
    await expect(page.locator('.cabecera-hoja nav a')).toHaveText(['Tierra', 'Tu lote', 'Rotaciones', 'Ciencia y validación', 'Datos abiertos', 'Fuentes'])
    await expect(page.getByRole('link', { name: 'Comenzar' })).toHaveAttribute('href', '#/tierra')
    await page.waitForTimeout(1800)
    const medidas = await medirContraste(page, TEXTOS)
    expect(medidas.filter((m) => m.contraste < m.minimo)).toEqual([])
  })
})
