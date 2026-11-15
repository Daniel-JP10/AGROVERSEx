// asistido por SI: Claude Code (Anthropic), E2E de Ciencia y validación sobre el build estático, en los tres motores
import { expect, test } from '@playwright/test'
import { ES, medirContraste, prohibidosEnTexto } from './marco_ayuda'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

// Derivación independiente del rango PI-D1 al umbral registrado (sin el lector de la app): control cruzado
function rangoRegistrado(): { min: number; max: number } {
  const inf = JSON.parse(readFileSync(join(process.cwd(), 'src', 'secciones', 'ciencia', 'pi_d1_mundo.json'), 'utf8'))
  const f = ['precipitacion_final', 'ndvi', 'humedad_radicular', 't2m'].map((k) => {
    const v = inf[k].todos_los_meses, u = v.unidades_con_mediana_de_la_dif_sobre_umbral.umbral
    const clave = v.tipo_diferencia === 'rel' ? `${Number((u * 100).toPrecision(6))}%` : `${u} K`
    return v.total.fraccion_mayor_a[clave] as number
  })
  return { min: Math.min(...f), max: Math.max(...f) }
}

const TEXTOS = ['main h1', 'main > p', '.tarjeta-hoja h2', '.tarjeta-hoja dt', '.tarjeta-hoja dd', '.tarjeta-hoja .nota', '.etiqueta-evidencia', '.limites li']

test('ciencia en inglés: ocho tarjetas, PI-D1 mundial con sus cifras del JSON y confianza sin dato, sin carbono; contraste AA', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 3200 })
  await page.goto('/#/ciencia')
  await expect(page.locator('[data-tarjeta]')).toHaveCount(8)
  // S1 integrado (V7, V8): la tarjeta muestra el rango al umbral registrado leído de pi_d1_mundo.json, nunca escrito a mano
  const r = rangoRegistrado()
  const cifra = page.locator('[data-tarjeta="pi_d1_mundo"] [data-campo="cifra"]')
  await expect(cifra).not.toHaveText(/Not available yet/)
  await expect(cifra).toContainText((r.min * 100).toFixed(1))
  await expect(cifra).toContainText((r.max * 100).toFixed(1))
  await expect(page.locator('[data-tarjeta="confianza"] [data-campo="cifra"]')).toHaveText(/Not available yet/)
  await expect(page.locator('[data-tarjeta="temperatura"]')).toContainText('WMO Resolution 40')
  const texto = await page.locator('main').innerText()
  expect(texto).not.toMatch(/carbon|carbono/i)
  expect(prohibidosEnTexto(texto)).toEqual([])
  const medidas = await medirContraste(page, TEXTOS)
  expect(medidas.length).toBeGreaterThan(40)
  expect(medidas.filter((m) => m.contraste < m.minimo)).toEqual([])
})

test.describe('español', () => {
  test.use({ storageState: ES })
  test('ciencia en español con sus tarjetas', async ({ page }) => {
    await page.goto('/#/ciencia')
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Ciencia y validación')
    await expect(page.locator('[data-tarjeta="confianza"]')).toContainText('Todavía no disponible')
  })
})
