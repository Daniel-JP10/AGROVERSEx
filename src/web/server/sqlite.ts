// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
/// <reference path="./node-sqlite.d.ts" />
import { DatabaseSync } from 'node:sqlite'

// Solo lectura estricta; mmap para que la coropleta ADM2 no copie la base.
export function abrirDb(ruta: string): DatabaseSync {
  const db = new DatabaseSync(ruta, { readOnly: true })
  db.exec('PRAGMA mmap_size=1073741824')
  return db
}
