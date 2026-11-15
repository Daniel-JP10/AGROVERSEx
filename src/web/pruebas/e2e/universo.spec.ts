// asistido por SI: Claude Code (Anthropic), e2e del universo: recorre las siete rutas y encuentra el globo en #/tierra
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

// Capturas de T-W0 en el árbol principal del repositorio (sale del worktree)
const CAPTURAS = resolve(process.cwd(), '../../../AGROVERSExz/repo/Docu/web/capturas/T-W0')
const RUTAS = [
  ['', 'portada', 'Inicio'],
  ['tierra', 'tierra', 'La Tierra desde el espacio'],
  ['gemelo', 'gemelo', 'El gemelo del lote'],
  ['rotaciones', 'rotaciones', 'Rotaciones'],
  ['ciencia', 'ciencia', 'Ciencia y validación'],
  ['datos', 'datos', 'Datos abiertos'],
  ['fuentes', 'fuentes', 'Fuentes, glosario y créditos'],
] as const

test('las siete rutas navegan, marcan la sección actual y muestran el aviso de apoyo', async ({ page }) => {
  for (const [ruta, nombre, enlace] of RUTAS) {
    await page.goto(`/#/${ruta}`)
    const actual = page.locator('nav a[aria-current="page"]')
    await expect(actual).toHaveCount(1)
    await expect(actual).toHaveText(enlace)
    await expect(page.locator('footer.pie')).toContainText('no reemplaza el criterio del agricultor ni del técnico')
    if (nombre === 'tierra') {
      await expect(page.locator('.mapa canvas.maplibregl-canvas')).toBeVisible()
    } else {
      // Portada y Fuentes ya tienen contenido (T-W1 y T-W3): su h1 es AGROVERSEx y el nombre de la sección, y no dicen "sin dato"
      await expect(page.getByRole('heading', { level: 1 })).toHaveText(nombre === 'portada' ? 'AGROVERSEx' : enlace)
      if (nombre === 'portada' || nombre === 'fuentes') await expect(page.getByRole('status')).toHaveCount(0)
      // Con VITE_EJEMPLOS=1 el gemelo pinta su ejemplo SIMULADO en lugar del aviso
      else if (nombre === 'gemelo' && process.env.VITE_EJEMPLOS === '1') await expect(page.getByText('SIMULADO').first()).toBeVisible()
      else await expect(page.getByRole('status')).toHaveText('Dato todavía no disponible.')
      await expect(page.locator('.mapa')).toHaveCount(0)
    }
    await page.waitForTimeout(nombre === 'tierra' ? 2500 : 200)
    // Las capturas de portada y Fuentes de T-W0 eran de secciones vacías; las nuevas van a capturas/T-W1_T-W3
    if (nombre !== 'portada' && nombre !== 'fuentes') await page.screenshot({ path: `${CAPTURAS}/${nombre}.png` })
  }
})

test('navegación con teclado: Tab llega a los enlaces y Enter cambia de sección', async ({ page }) => {
  await page.goto('/#/')
  const gemelo = page.getByRole('link', { name: 'El gemelo del lote' })
  for (let i = 0; i < 10 && !(await gemelo.evaluate((e) => e === document.activeElement)); i++) await page.keyboard.press('Tab')
  await expect(gemelo).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/#\/gemelo$/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('El gemelo del lote')
})

test('el globo vuelve a montarse al regresar a #/tierra y la ruta desconocida va a la portada', async ({ page }) => {
  await page.goto('/#/tierra')
  await expect(page.locator('.mapa canvas.maplibregl-canvas')).toBeVisible()
  await page.getByRole('link', { name: 'Datos abiertos' }).click()
  await expect(page.locator('.mapa')).toHaveCount(0)
  await page.getByRole('link', { name: 'La Tierra desde el espacio' }).click()
  await expect(page.locator('.mapa canvas.maplibregl-canvas')).toBeVisible()
  await page.goto('/#/no-existe')
  await expect(page.locator('nav a[aria-current="page"]')).toHaveText('Inicio')
})
