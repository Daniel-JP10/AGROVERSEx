// asistido por SI: Claude Code (Anthropic), detector de rutas locales: Fuentes filtra las celdas y la prueba de dist lo reutiliza
// Sin bandera i: la letra de unidad se escribe con [A-Za-z] y lo demás tal cual
const PATRONES: [string, RegExp][] = [
  // Letra de unidad con / o \ (también escapada \\) al inicio o tras espacio, comilla, paréntesis, corchete, = o >;
  // así https:// y el código minificado (a?o:/re/, {b:/re/}) no cuentan
  ['unidad', /(?:^|(?<=[\s"'`(\[=>]))[A-Za-z]:(?:\\{1,2}|\/)(?=[A-Za-z0-9_.$~%-])/],
  // Las etiquetas no repiten la ruta: este archivo también se compila y la prueba de dist lo leería
  ['mnt', /\/mnt\//],
  ['tmp', /\/tmp\//],
  ['root', /\/root\//],
  ['Users', /\/Users\//],
  // Ruta UNC en texto plano (\\servidor\) o escapada en JS/JSON (\\\\servidor)
  // \\u00C0 de una clase de caracteres minificada no es un servidor
  ['UNC', /(?<!\\)\\\\(?!u[0-9A-Fa-f]{4})[A-Za-z][\w.$-]*\\/],
  ['UNC escapada', /\\\\\\\\(?!u[0-9A-Fa-f]{4})[A-Za-z][\w.$-]*\\\\/],
  ['carpeta de despliegue', /herramientas-desplieg(?:ue)/],
]

/** Primera ruta local que aparece en el texto, o null. */
export function rutaLocalEn(texto: string): { patron: string; indice: number } | null {
  let mejor: { patron: string; indice: number } | null = null
  for (const [patron, re] of PATRONES) {
    const m = re.exec(texto)
    if (m && (!mejor || m.index < mejor.indice)) mejor = { patron, indice: m.index }
  }
  return mejor
}

/** Celda apta para publicarse: sin ninguna ruta local. */
export const sinRutaLocal = (celda: string) => rutaLocalEn(celda) === null
