// asistido por SI: Claude Code (Anthropic), petición que usa PanelRegion mientras exista /api/rotaciones en desarrollo local
// shortcut: solo para el servidor de desarrollo; desaparece cuando PanelRegion lea lotes_demo.json (web_componentes §7)
export interface RespRotaciones { vacio: boolean; motivo?: string; zona?: string }

export async function pedirRotaciones(unidad: string, f: typeof fetch = fetch): Promise<RespRotaciones> {
  const r = await f(`/api/rotaciones?unidad=${encodeURIComponent(unidad)}`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}
