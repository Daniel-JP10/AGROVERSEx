// asistido por SI: Claude Code (Anthropic), pruebas de la entrada #/ (plan v2 §2): frase, raíces, seis nodos navegables y Start
import { readFileSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, describe, expect, it } from 'vitest'
import { NODOS, Portada } from '../src/secciones/portada/Portada'
import { alternar, idioma } from '../src/textos/i18n'
import * as portada from '../src/textos/secciones/portada'

afterEach(() => { if (idioma() !== 'en') alternar() })
const html = () => renderToStaticMarkup(createElement(Portada))
const esc = (s: string) => s.replace(/'/g, '&#x27;')

describe('entrada', () => {
  it('AGROVERSEx al centro con la frase del director, en inglés por defecto y en español', () => {
    let h = html()
    // R1: la x va en un span más pequeño; el nombre accesible sigue siendo AGROVERSEx
    expect(h).toContain('<h1 class="titulo-marca">AGROVERSE<span class="x">x</span></h1>')
    expect(h).toContain('Your land through NASA open data, from space down to your field.')
    expect(h).toContain('Compare rotations with a digital twin that shows ranges, not promises.')
    alternar()
    h = html()
    expect(h).toContain('Tu tierra vista con datos abiertos de la NASA, del espacio a tu lote.')
    expect(h).toContain('Compara rotaciones con un gemelo digital que muestra rangos, no promesas.')
  })
  it('seis nodos <a href> en orden del reloj, cada uno con su nombre visible', () => {
    const h = html()
    const nodos = [...h.matchAll(/<a class="nodo" data-nodo="(\w+)" href="([^"]+)"[^>]*>(.*?)<\/a>/g)]
    expect(nodos.map((m) => m[2])).toEqual(['#/tierra', '#/lote', '#/rotaciones', '#/ciencia', '#/datos', '#/fuentes'])
    for (const m of nodos) expect(m[3].replace(/<[^>]+>/g, '').trim().length, m[1]).toBeGreaterThan(3)
    expect(h).toContain(esc("Your field's twin"))
    // Orden del reloj: ángulos crecientes desde arriba a la izquierda
    // Con y hacia abajo, atan2 crece en el sentido del reloj; se mide desde el primer nodo
    const crudo = NODOS.map((n) => Math.atan2(n.y - 300, n.x - 500) * 180 / Math.PI)
    const ang = crudo.map((a) => (a - crudo[0] + 360) % 360)
    expect([...ang].sort((a, b) => a - b)).toEqual(ang)
  })
  it('Earth y el lote usan sus imágenes con alt vacío (el nombre lo da el texto); los demás, íconos SVG ocultos', () => {
    const h = html()
    expect(h).toMatch(/<img class="figura-nodo" src="\/portada\/globo\.webp" alt=""/)
    expect(h).toMatch(/<img class="figura-nodo" src="\/lotes\/bloque_DEMO-COL-01\.webp" alt=""/)
    // R1: los otros cuatro nodos llevan ilustraciones SVG con volumen, todas decorativas
    const ilus = h.match(/<svg[^>]*class="ilustracion"[^>]*>/g) ?? []
    expect(ilus).toHaveLength(4)
    for (const s of ilus) expect(s).toContain('aria-hidden="true"')
  })
  it('raíces SVG decorativas, una por nodo, y Start a #/tierra', () => {
    const h = html()
    expect(h).toMatch(/<svg class="raices"[^>]*aria-hidden="true"/)
    expect((h.match(/class="raiz"/g) ?? []).length).toBe(6)
    expect(h).toMatch(/<a class="boton-principal comenzar" href="#\/tierra">Start<\/a>/)
  })
  it('sin insignia NASA, ERA5 ni cifras en la entrada', () => {
    const texto = html().replace(/<svg[\s\S]*?<\/svg>/g, '').replace(/<[^>]+>/g, ' ').replace(/&#x27;/g, "'")
    expect(texto).not.toMatch(/ERA5|logo|insignia/i)
    expect(texto).not.toMatch(/\d/)
  })
  it('las raíces crecen con stroke-dashoffset y no se animan con prefers-reduced-motion', () => {
    const css = readFileSync(new URL('../src/secciones/portada/portada.css', import.meta.url), 'utf8')
    expect(css).toMatch(/@keyframes raiz-crece \{ from \{ stroke-dashoffset: 1; \}/)
    // R1: el bloque de movimiento reducido detiene raíces, ramas, hojas, halo y flotación
    const reducido = css.slice(css.indexOf('@media (prefers-reduced-motion: reduce)'))
    for (const sel of ['.portada .raiz,', '.portada .rama,', '.portada .hoja-r,', '.portada .halo-luz,', '.portada .nodo .figura,']) expect(reducido.split('animation: none')[0], sel).toContain(sel)
    expect(css).toMatch(/\.portada \.raices \{[^}]*pointer-events: none/)
  })
  it('la savia luminosa se dibuja con movimiento y no con prefers-reduced-motion', () => {
    expect((html().match(/class="savia"/g) ?? []).length).toBe(12)
    const original = globalThis.matchMedia
    globalThis.matchMedia = ((q: string) => ({ matches: q.includes('reduce'), addEventListener() {}, removeEventListener() {} })) as unknown as typeof matchMedia
    try { expect(html()).not.toContain('class="savia"') } finally { globalThis.matchMedia = original }
  })
  it('la ilustración de Ciencia dibuja las 36 barras de la fracción HLS válida, leídas del archivo', async () => {
    const { BARRAS_HLS } = await import('../src/secciones/portada/iconos')
    const hls = JSON.parse(readFileSync(new URL('../../../datos/lotes/hls_validez_DEMO-USA-01.json', import.meta.url), 'utf8'))
    expect(BARRAS_HLS).toEqual(Object.keys(hls.meses).sort().map((m) => hls.meses[m].media))
    expect(BARRAS_HLS).toHaveLength(36)
    expect(html()).toContain('data-fuente="datos/lotes/hls_validez_DEMO-USA-01.json · meses.*.media"')
  })
  it('textos de la portada: EN y ES con las mismas claves y sin dígitos', () => {
    expect(Object.keys(portada.es).sort()).toEqual(Object.keys(portada.en).sort())
    for (const v of [...Object.values(portada.en), ...Object.values(portada.es)]) expect(v).not.toMatch(/\d/)
  })
})
