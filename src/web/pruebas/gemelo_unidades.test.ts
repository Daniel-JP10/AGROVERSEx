// asistido por SI: Claude Code (Anthropic), prueba que fija unidades de trayectoria_mensual y el mes 0 contra contrato, código y paquetes
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { FLUJOS, MES_0, UNIDADES_TRAYECTORIA, indiceMes } from '../src/secciones/lote/unidades'

const RAIZ = join(__dirname, '..', '..', '..')
const leer = (r: string) => readFileSync(join(RAIZ, r), 'utf8')
const GEMELO = join(__dirname, '..', 'public', 'gemelo')

describe('unidades de trayectoria_mensual (contratos/gemelo_api.md v1.2)', () => {
  const contrato = leer('contratos/gemelo_api.md')
  const fila = contrato.split('\n').find((l) => l.startsWith('| `trayectoria_mensual`'))!
  it('el contrato es la v1.2 y declara la fila', () => {
    expect(contrato).toContain('version_contrato_completa = "1.2"')
    expect(fila).toBeDefined()
  })
  it('cada estado dibujado tiene la unidad del contrato, como media del mes', () => {
    expect(fila).toContain('Estados (media del mes)')
    for (const [v, u] of Object.entries(UNIDADES_TRAYECTORIA)) {
      if (FLUJOS.includes(v as never)) continue
      expect(fila, v).toContain(`\`${v}\` ${u}`)
    }
  })
  it('P y ETa son flujos en mm, suma del mes', () => {
    expect(fila).toMatch(/Flujos \(suma del mes, mm o kg N\/ha\): `P`, `ETa`/)
    for (const v of FLUJOS) expect(UNIDADES_TRAYECTORIA[v]).toBe('mm')
  })
  it('el código del gemelo arma estados como media y flujos como suma', () => {
    const ind = leer('src/gemelo/indicadores.py')
    expect(ind).toContain('for k in ("W", "agua_raiz", "N", "C", "B", "V", "desnudo"):')
    expect(ind).toContain('for k in ("P", "ETa", "I_bruto", "D", "R", "L_lix"):')
    expect(leer('src/gemelo/agua.py')).toContain('W = W1 + W2 en mm')
    expect(leer('src/gemelo/agua.py')).toContain('Agua disponible relativa (0 en punto de marchitez, 1 en capacidad de campo)')
  })
})

describe('mes 0 de los arreglos mensuales', () => {
  it('es enero del año 1 según el código', () => {
    expect(MES_0).toBe('enero_anio_1')
    expect(leer('src/gemelo/clima.py')).toContain('DIAS_MES = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])')
    expect(leer('src/gemelo/clima.py')).toContain('MES_DE_DIA = np.repeat(np.arange(12), DIAS_MES)')
    expect(leer('src/gemelo/indicadores.py')).toContain('mes = (np.arange(H)[:, None] * 12 + MES_DE_DIA[None, :]).reshape(-1)')
    expect(leer('src/gemelo/modelos.py')).toContain('(0 = 1 de enero del año 1)')
    expect(indiceMes(1, 0)).toBe(0)
    expect(indiceMes(3, 11)).toBe(35)
  })
  // Prueba física: sin cultivo antes de la primera siembra la cobertura viva es 0; si el índice 0 fuera la siembra, no lo sería
  const lotes = readdirSync(GEMELO).filter((d) => /^DEMO-/.test(d))
  for (const lote of lotes) for (const f of readdirSync(join(GEMELO, lote)).filter((x) => x.startsWith('simulacion_'))) {
    it(`${lote}/${f}: 12 x horizonte meses, rangos físicos y cobertura nula antes de la siembra`, () => {
      const doc = JSON.parse(readFileSync(join(GEMELO, lote, f), 'utf8'))
      const n = 12 * doc.metadatos.horizonte_anios
      for (const e of doc.estrategias) {
        for (const v of Object.keys(UNIDADES_TRAYECTORIA)) for (const q of ['p10', 'p50', 'p90']) {
          const xs: number[] = e.trayectoria_mensual[v][q]
          expect(xs, `${e.id} ${v} ${q}`).toHaveLength(n)
          expect(xs.every((x) => Number.isFinite(x) && x >= 0)).toBe(true)
          if (UNIDADES_TRAYECTORIA[v as keyof typeof UNIDADES_TRAYECTORIA] === 'fracción') expect(xs.every((x) => x <= 1)).toBe(true)
        }
        const m = /^A1-(\d\d)-/.exec(e.temporadas[0].siembra)
        if (!m) continue
        const mesSiembra = Number(m[1]) - 1
        for (let i = 0; i < mesSiembra; i++) expect(e.trayectoria_mensual.V.p90[i], `${e.id} mes ${i}`).toBe(0)
        expect(Math.max(...e.trayectoria_mensual.V.p50.slice(mesSiembra, mesSiembra + 4))).toBeGreaterThan(0)
      }
    })
  }
})
