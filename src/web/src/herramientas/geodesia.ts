import { t } from '../textos/i18n'
// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Geodesia de la herramienta Medir. Puntos en [lon, lat] (grados), como GeoJSON.
// shortcut: esfera de radio medio (haversine y área esférica), error de hasta ~0,5 % frente al elipsoide; subir a Vincenty/WGS84 si la cifra va a una ficha oficial.
/** Error máximo declarado de la esfera frente al elipsoide, en %; el texto de Medir lo muestra desde aquí (cifras.ts, atada por prueba) */
export const ERROR_ESFERA_PCT = 0.5

const R_KM = 6371.0088
const rad = (g: number) => (g * Math.PI) / 180

/** Distancia de círculo máximo entre dos puntos, en km (haversine). */
export function distanciaKm(a: [number, number], b: [number, number]): number {
  const [lon1, lat1, lon2, lat2] = [rad(a[0]), rad(a[1]), rad(b[0]), rad(b[1])]
  const h = Math.sin((lat2 - lat1) / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin((lon2 - lon1) / 2) ** 2
  return 2 * R_KM * Math.asin(Math.min(1, Math.sqrt(h)))
}

/** Área de un anillo sobre la esfera, en km² (fórmula de Chamberlain y Duquette). */
export function areaKm2(anillo: [number, number][]): number {
  if (anillo.length < 3) throw new Error(t('medir.anillo'))
  const n = anillo.length
  let suma = 0
  for (let i = 0; i < n; i++) {
    const [l1, f1] = [rad(anillo[i][0]), rad(anillo[i][1])]
    const [l2, f2] = [rad(anillo[(i + 1) % n][0]), rad(anillo[(i + 1) % n][1])]
    let dl = l2 - l1
    if (dl > Math.PI) dl -= 2 * Math.PI // cruce del antimeridiano
    if (dl < -Math.PI) dl += 2 * Math.PI
    suma += dl * (2 + Math.sin(f1) + Math.sin(f2))
  }
  return (Math.abs(suma) * R_KM ** 2) / 2
}
