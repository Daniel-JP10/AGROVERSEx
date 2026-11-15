// asistido por SI: Claude Code (Anthropic), copia reproducible de los paquetes del gemelo y del relieve de los lotes a public/
// Uso, desde src/web: node herramientas/copiar_gemelo.mjs [carpeta de datos/publicos/gemelo]
// Copia solo indice.json, textos/ y de cada lote lote.json, simulacion_*.json y optimizacion_*.json (sin calibracion/ ni personalizados/)
import { copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync, rmSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const WEB = join(dirname(fileURLToPath(import.meta.url)), '..')
const RAIZ = join(WEB, '..', '..')
const origen = process.argv[2] ?? join(RAIZ, 'datos', 'publicos', 'gemelo')
const destino = join(WEB, 'public', 'gemelo')
const ARCHIVO_LOTE = /^(lote|simulacion_[a-z_]+|optimizacion_[a-z_]+)\.json$/

// Se borra el destino para que no queden archivos viejos
if (existsSync(destino)) rmSync(destino, { recursive: true })
mkdirSync(join(destino, 'textos'), { recursive: true })
// indice.json sin nota_naturaleza: es una nota interna que contiene una palabra de la lista de textos prohibidos; la app no la lee
const ind = JSON.parse(readFileSync(join(origen, 'indice.json'), 'utf8'))
delete ind.nota_naturaleza
writeFileSync(join(destino, 'indice.json'), JSON.stringify(ind, null, 1) + '\n')
for (const f of readdirSync(join(origen, 'textos')).filter((f) => f.endsWith('.json'))) copyFileSync(join(origen, 'textos', f), join(destino, 'textos', f))
const indice = JSON.parse(readFileSync(join(origen, 'indice.json'), 'utf8'))
let n = 0
for (const { lote_id } of indice.lotes) {
  if (!/^DEMO-[A-Z]{3}-\d{2}$/.test(lote_id)) throw new Error(`lote_id inválido ${lote_id}`)
  mkdirSync(join(destino, lote_id))
  for (const f of readdirSync(join(origen, lote_id)).filter((f) => ARCHIVO_LOTE.test(f)).sort()) {
    copyFileSync(join(origen, lote_id, f), join(destino, lote_id, f)); n++
  }
}

// Relieve de los lotes: solo el bloque relieve_nasadem_30m de la exposición erosiva (elevación y pendiente)
const expo = JSON.parse(readFileSync(join(RAIZ, 'datos', 'lotes', 'exposicion_erosiva_lotes.json'), 'utf8'))
const relieve = { fuente: 'datos/lotes/exposicion_erosiva_lotes.json', version: expo.version, lotes: {} }
for (const [id, l] of Object.entries(expo.lotes)) relieve.lotes[id] = l.relieve_nasadem_30m
mkdirSync(join(WEB, 'public', 'lotes'), { recursive: true })
writeFileSync(join(WEB, 'public', 'lotes', 'relieve_lotes.json'), JSON.stringify(relieve, null, 1) + '\n')
console.log(`gemelo: ${n} archivos de lote copiados; relieve de ${Object.keys(relieve.lotes).length} lotes`)
