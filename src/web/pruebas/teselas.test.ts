// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import http from 'node:http'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import type { AddressInfo } from 'node:net'
import { servirTeselas } from '../server/teselas'

let srv: http.Server, base = '', dir = ''
beforeAll(async () => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tes-'))
  fs.mkdirSync(path.join(dir, 'teselas'))
  fs.writeFileSync(path.join(dir, 'teselas', 'adm0.pmtiles'), Buffer.from(Array.from({ length: 64 }, (_, i) => i)))
  fs.writeFileSync(path.join(dir, 'secreto.txt'), 'no')
  process.env.AGROVERSEX_DATOS = dir
  // Se invoca el middleware del plugin directamente
  let mw: (req: http.IncomingMessage, res: http.ServerResponse, next: () => void) => void = () => {}
  const p = servirTeselas() as unknown as { configureServer: (s: unknown) => void }
  p.configureServer({ middlewares: { use: (f: typeof mw) => { mw = f } } })
  srv = http.createServer((q, r) => mw(q, r, () => { r.statusCode = 404; r.end() }))
  await new Promise<void>((ok) => srv.listen(0, ok))
  base = `http://127.0.0.1:${(srv.address() as AddressInfo).port}`
})
afterAll(() => { srv.close(); fs.rmSync(dir, { recursive: true, force: true }) })

describe('servirTeselas', () => {
  it('Range bytes=0-15 devuelve 206 con Content-Range', async () => {
    const r = await fetch(`${base}/teselas/adm0.pmtiles`, { headers: { Range: 'bytes=0-15' } })
    expect(r.status).toBe(206)
    expect(r.headers.get('content-range')).toBe('bytes 0-15/64')
    expect((await r.arrayBuffer()).byteLength).toBe(16)
  })
  it('sin Range devuelve 200 completo', async () => {
    const r = await fetch(`${base}/teselas/adm0.pmtiles`)
    expect(r.status).toBe(200)
    expect((await r.arrayBuffer()).byteLength).toBe(64)
  })
  it('nombre desconocido o traversal da 404', async () => {
    for (const u of ['/teselas/otro.pmtiles', '/teselas/..%2fsecreto.txt', '/teselas/../secreto.txt', '/teselas/adm1.pmtiles']) {
      expect((await fetch(`${base}${u}`)).status).toBe(404)
    }
  })
})
