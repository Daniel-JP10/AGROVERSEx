// asistido por SI: Claude Code (Anthropic), ayudas de los E2E de W1: idioma sembrado, contraste medido sobre el fondo real y textos prohibidos
import type { Page } from '@playwright/test'

// El origen sigue al puerto del config (E2E_ORIGEN); por defecto 5199 como antes
export const ORIGEN = process.env.E2E_ORIGEN ?? 'http://localhost:5199'
export const ES = { cookies: [], origins: [{ origin: ORIGEN, localStorage: [{ name: 'agroversex-idioma', value: 'es' }] }] }

// Lista de la fase 3 (misma que textos_prohibidos.test.ts), aplicada al texto que se ve
export const PROHIBIDOS_F3: [string, RegExp][] = [
  ['NASA logo', /NASA logo|logo de la NASA|logo NASA/], ['ERA5', /ERA5/], ['GAEZ', /\bGAEZ\b/], ['CDL', /\bCDL\b/],
  ['live', /(?<![-\w])[Ll]ive\b/], ['en vivo', /[Ee]n vivo/], ['Telemetr', /[Tt]elemetr/], ['Salud del lote', /[Ss]alud del lote/],
  ['Lot health', /[Ll]ot health/], ['Pred.', /\bPred\./], ['fps', /\bfps\b/],
]
export const prohibidosEnTexto = (t: string) => PROHIBIDOS_F3.filter(([, re]) => re.test(t)).map(([n]) => n)

export type Medida = { selector: string; texto: string; contraste: number; minimo: number }

/**
 * Contraste de cada texto contra el fondo real: se hace una captura con el texto transparente (las sombras y brillos
 * se conservan) y se toma el peor píxel de una rejilla en la banda central de la caja (del 15 al 85 % en x y del 25 al 75 % en y),
 * para no muestrear bordes ni esquinas redondeadas.
 */
export async function medirContraste(page: Page, selectores: string[]): Promise<Medida[]> {
  const cajas = await page.evaluate((sels) => {
    const out: { selector: string; texto: string; color: string; grande: boolean; x: number; y: number; w: number; h: number }[] = []
    for (const s of sels) for (const el of Array.from(document.querySelectorAll<HTMLElement>(s))) {
      const r = el.getBoundingClientRect()
      const cs = getComputedStyle(el)
      // Solo lo que está entero en la ventana: lo de fuera no se puede muestrear contra su fondo real
      if (!r.width || !r.height || cs.visibility === 'hidden' || !el.innerText.trim()) continue
      if (r.top < 0 || r.left < 0 || r.bottom > window.innerHeight || r.right > window.innerWidth) continue
      // Dentro de un contenedor con desplazamiento, solo si se ve en él
      const caja = el.closest('.tabla-scroll, main')?.getBoundingClientRect()
      if (caja && (r.top < caja.top || r.bottom > caja.bottom || r.left < caja.left || r.right > caja.right)) continue
      const px = parseFloat(cs.fontSize), peso = Number(cs.fontWeight) || 400
      out.push({ selector: s, texto: el.innerText.trim().slice(0, 40), color: cs.color, grande: px >= 24 || (px >= 18.66 && peso >= 700), x: r.x, y: r.y, w: r.width, h: r.height })
    }
    return out
  }, selectores)
  const estilo = await page.addStyleTag({ content: '* { color: transparent !important; caret-color: transparent !important; }' })
  const png = (await page.screenshot({ animations: 'disabled' })).toString('base64')
  await estilo.evaluate((n) => (n as Element).remove())
  return page.evaluate(async ({ png, cajas }) => {
    const img = new Image()
    img.src = `data:image/png;base64,${png}`
    await img.decode()
    const c = document.createElement('canvas')
    c.width = img.naturalWidth; c.height = img.naturalHeight
    const ctx = c.getContext('2d')!
    ctx.drawImage(img, 0, 0)
    const escala = img.naturalWidth / window.innerWidth
    const lin = (v: number) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
    const luz = (r: number, g: number, b: number) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    const ratio = (a: number, b: number) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
    return cajas.map((k) => {
      const [r, g, b] = k.color.match(/[\d.]+/g)!.map(Number)
      const lt = luz(r, g, b)
      let peor = Infinity
      for (let i = 0; i <= 4; i++) for (let j = 0; j <= 2; j++) {
        const x = Math.round((k.x + k.w * (0.15 + 0.7 * i / 4)) * escala), y = Math.round((k.y + k.h * (0.25 + 0.5 * j / 2)) * escala)
        if (x < 0 || y < 0 || x >= c.width || y >= c.height) continue
        const d = ctx.getImageData(x, y, 1, 1).data
        peor = Math.min(peor, ratio(lt, luz(d[0], d[1], d[2])))
      }
      return { selector: k.selector, texto: k.texto, contraste: Math.round(peor * 100) / 100, minimo: k.grande ? 3 : 4.5 }
    })
  }, { png, cajas })
}
