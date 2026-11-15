// asistido por SI: Claude Code (Anthropic), unidades de trayectoria_mensual y significado del mes 0 (condición 3 del director)
// Fuente: contratos/gemelo_api.md v1.2, fila trayectoria_mensual; lo ata pruebas/gemelo_unidades.test.ts
// Estados como media del mes; P y ETa como suma del mes. Variable que no está aquí no se dibuja.
export const UNIDADES_TRAYECTORIA = {
  W: 'mm', agua_raiz: 'fracción', N: 'kg N/ha', V: 'fracción', desnudo: 'fracción', P: 'mm', ETa: 'mm',
} as const
export type VariableTrayectoria = keyof typeof UNIDADES_TRAYECTORIA
export const FLUJOS: readonly VariableTrayectoria[] = ['P', 'ETa']
// Índice 0 de los arreglos mensuales = enero del año 1 del horizonte (src/gemelo/clima.py MES_DE_DIA y
// modelos.dia_nominal: día 0 = 1 de enero del año 1); el índice 12(a-1)+m es el mes m (0 = enero) del año a
export const MES_0 = 'enero_anio_1' as const
export const indiceMes = (anio: number, mes: number) => 12 * (anio - 1) + mes
