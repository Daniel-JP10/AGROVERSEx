// asistido por SI: Claude Code (Anthropic), ningún texto de la interfaz lleva el marcador PENDING o PENDIENTE (director 21:54)
import { describe, expect, it } from 'vitest'
import { enTodo, esTodo } from '../src/textos/indice'

// lotes.riesgo.* solo se ve con la API (pestaña Lotes de PanelRegion, rot?.zona viene de /api/rotaciones); el build público no la muestra
const SOLO_API = /^lotes\.riesgo\./
// Marcador en mayúsculas: "pendiente" en minúsculas es la inclinación del terreno y es legítimo
const MARCADOR = /\bPENDING\b|\bPENDIENTES?\b/

describe('textos sin marcador de pendiente', () => {
  it('ningún texto EN ni ES visible lleva PENDING o PENDIENTE', () => {
    const malos = [...Object.entries(enTodo), ...Object.entries(esTodo)]
      .filter(([k, v]) => !SOLO_API.test(k) && typeof v === 'string' && MARCADOR.test(v))
      .map(([k]) => k)
    expect(malos).toEqual([])
  })
})
