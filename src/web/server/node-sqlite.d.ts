// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Tipos mínimos de node:sqlite (el proyecto no instala @types/node).
declare module 'node:sqlite' {
  export class StatementSync {
    all(...p: unknown[]): Record<string, unknown>[]
    get(...p: unknown[]): Record<string, unknown> | undefined
    run(...p: unknown[]): unknown
  }
  export class DatabaseSync {
    constructor(ruta: string, opts?: { readOnly?: boolean })
    exec(sql: string): void
    prepare(sql: string): StatementSync
    close(): void
  }
}
