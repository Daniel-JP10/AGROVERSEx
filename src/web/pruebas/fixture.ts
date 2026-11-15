// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { DatabaseSync } from 'node:sqlite'
import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

// Base mínima con el DDL real de la fase 2 (esquema_geo.sql + esquema_agroversex.sql).
const ddl = (f: string) => readFileSync(new URL(`../../simulacion/${f}`, import.meta.url), 'utf8')

export const UNIDADES = [
  ['AAA', 0], ['BBB', 0], ['AAA.1_1', 1], ['BBB.1_1', 1], ['AAA.1.1_1', 2], ['BBB.1.1_1', 2],
] as const

// Devuelve la ruta de una base temporal; el hueco es AAA.1_1 en el mes 2 (NULL con bandera 1).
export function crearFixture(): string {
  const ruta = join(mkdtempSync(join(tmpdir(), 'agroversex-api-')), 'agroversex.sqlite')
  const db = new DatabaseSync(ruta)
  db.exec(ddl('geo/esquema_geo.sql'))
  db.exec(ddl('esquema_agroversex.sql'))
  db.exec(`INSERT INTO variable(id,nombre,escala,desplazamiento,valido_min,valido_max,etiqueta) VALUES
    ('precip','Lluvia',0.001,0,0,50,'FUENTE'),('precip_frac','Fracción',0.001,0,0,1,'SUPUESTO'),
    ('t2m','Temperatura',0.01,0,-60,60,'FUENTE'),('elev_media','Elevación',NULL,NULL,-500,9000,'real_contexto')`)
  const u = db.prepare('INSERT INTO unidad(id,nivel,iso3,padre_id,nombre,bbox_oeste,bbox_sur,bbox_este,bbox_norte) VALUES(?,?,?,?,?,?,?,?,?)')
  for (const [id, n] of UNIDADES) u.run(id, n, id.slice(0, 3), n ? id.replace(/\.1.*/, '') : null, `n-${id}`, -1, -1, 1, 1)
  const m = db.prepare('INSERT INTO mensual(unidad_id,mes_id,precip,precip_frac,t2m,bandera_motivo) VALUES(?,?,?,?,?,?)')
  UNIDADES.forEach(([id], i) => {
    for (let mes = 0; mes < 4; mes++) {
      const hueco = id === 'AAA.1_1' && mes === 2
      m.run(id, mes, hueco ? null : 100 * (i + 1) + mes, hueco ? 0 : 1000, 2300 + i, hueco ? 1 : 0)
    }
  })
  db.exec(`INSERT INTO estatico VALUES('AAA','elev_media',NULL,NULL,NULL,1234.5,0.9)`)
  db.exec(`INSERT INTO clase_fraccion VALUES('AAA','igbp','12',0.5)`)
  db.exec(`UPDATE variable SET unidad_medida='mm/h' WHERE id='precip'`)
  db.exec(`INSERT INTO variable(id,nombre,escala,desplazamiento,valido_min,valido_max,etiqueta,unidad_medida) VALUES
    ('ndvi',NULL,0.0001,0,-0.2,1,'FUENTE','adim'),('nbr2',NULL,0.0001,0,-1,1,'FUENTE','adim'),('sm_verdad',NULL,0.001,0,0,0.9,'SUPUESTO','m3/m3'),
    ('t2m_p10','t2m p10',0.01,0,-60,60,'FUENTE','C'),('t2m_p90','t2m p90',0.01,0,-60,60,'FUENTE','C')`)
  db.exec(`INSERT INTO enso VALUES(2,0.5,0.4),(0,-1.5,-1.4),(1,-1.2,-1.1)`)
  db.exec(`INSERT INTO evento VALUES('e1','Sequia',2010,2010,'Region A','mag',NULL,'FUENTE')`)
  db.exec(`INSERT INTO evento_unidad VALUES('e1','AAA',0.7)`)
  db.exec(`INSERT INTO anual(unidad_id,anio,cobertura_igbp) VALUES('AAA',2000,10),('AAA',2001,12)`)
  db.exec(`INSERT INTO sistema_rotacion VALUES('s1','n-AAA','Maiz-soya','alt1',NULL,'EV-1','FUENTE'),
    ('s2','Otra','X',NULL,NULL,NULL,'PENDIENTE'), ('s3','Corn Belt','Maiz-soya',NULL,NULL,'EV-1','FUENTE')`)
  db.exec(`INSERT INTO zona_demo VALUES('AAA.1.1_1','corn_belt')`)
  db.exec(`INSERT INTO efecto_antecesor VALUES('n-AAA','S','C',2.5,-3.4,0.6,-1.0,15,'EV-1')`)
  db.exec(`INSERT INTO efecto_antecesor VALUES('EE. UU.','S','C',0.9,0.7,1.3,-1.6,1,'EV-1')`)
  db.exec(`INSERT INTO cultivo(id,nombre,etiqueta) VALUES('c1','Maiz','FUENTE')`)
  db.exec(`INSERT INTO regla_sucesion VALUES('Papa','Verticillium',3,4,'templado','EV-2')`)
  db.exec(`INSERT INTO lote VALUES('L1','AAA.1.1_1','POLYGON((0 0,1 0,1 1,0 0))','papa','demo')`)
  db.exec(`INSERT INTO lote_diario VALUES('L1',0,5000,-200,300,NULL,0)`)
  db.close()
  return ruta
}
