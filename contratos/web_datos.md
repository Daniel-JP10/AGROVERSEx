# Contrato web_datos · v0 (2026-11-14, T-D9 / T-D7 Parte C)

Estado: v0 publicada con los archivos estáticos reales de Colombia (`COL`, 1.156 unidades: 1 ADM0, 33 ADM1, 1.122 ADM2), geometría de encuadre mundial (`unidades_geo.json.gz`), catálogo público de lotes DEMO (`lotes_demo.json`, D-027) y manifiesto con sumas SHA-256 (`manifiesto.json`). Lo consume `src/web/src/datos/estatico.ts` sin servidor (`D-014`). Rótulos: VERIFICADO, FUENTE, INFERENCIA, SUPUESTO, PENDIENTE.

## 1. Rutas públicas y prefijo de despliegue

Todos los archivos viven en `src/web/public/datos/` y se piden en el navegador mediante `rutaPublica('datos/...')` (`${import.meta.env.BASE_URL}datos/...`), de modo que funcionan tanto en la raíz (`/`) como bajo un subcamino de alojamiento estático (`/AGROVERSEx/`).

| Ruta relativa a `public/` | Formato | Contenido |
|-|-|-|
| `datos/<iso3>/<variable>_<nivel>.json.gz` | JSON comprimido con gzip (`mtime=0`, nivel 9) | Matriz `unidades × meses` de una variable (`precip`, `sm_raiz`, `t2m`, `ndvi`) y un nivel (`0`, `1`, `2`) para el país `<iso3>` (`COL` en v0) |
| `datos/unidades_geo.json.gz` | JSON comprimido con gzip (`mtime=0`, nivel 9) | Diccionario `unidad_id -> [oeste, sur, este, norte, padre_id]` (más `[punto_lon, punto_lat]` si cruza el antimeridiano) para las unidades reales de `unidades.gpkg` |
| `datos/lotes_demo.json` | JSON UTF-8 | Copia pública exacta de `datos/lotes/lotes_demo.json` (D-027) con `DEMO-USA-01` y `DEMO-COL-01` |
| `datos/meta.json` | JSON UTF-8 | Resumen de país, eje temporal, variables, niveles, meses disponibles y productos |
| `datos/manifiesto.json` | JSON UTF-8 | Versión del contrato, fecha UTC de generación, variables y meses disponibles, tamaño en bytes y hash `sha256` de cada archivo público |

## 2. Esquema de `datos/<iso3>/<variable>_<nivel>.json.gz`

Cada archivo contiene un objeto JSON con las siguientes claves (VERIFICADO contra `src/mapa_estatico/construir.py` y `src/web/src/datos/estatico.ts`):

| Clave | Tipo | Descripción |
|-|-|-|
| `formato` | texto | `"web_datos v0"` |
| `variable` | texto | Identificador de capa en el globo: `"precip"`, `"sm_raiz"`, `"t2m"` o `"ndvi"` |
| `nivel` | entero `0`, `1` o `2` | Nivel administrativo de CGAZ (`contratos/unidades.md`) |
| `ponderacion` | texto | `"area"` (media ponderada por área de celda y fracción cubierta de la unidad, `contratos/serie_mensual.md`) |
| `mes0` | texto | `"2000-01"` (índice `0` del eje temporal UTC) |
| `n_meses` | entero | `323` (`2000-01` a `2026-11` inclusive) |
| `ids` | `string[]` | Lista ordenada de `unidad_id` (`len(ids)` = `1` en nivel 0, `33` en nivel 1, `1122` en nivel 2 para `COL`) |
| `productos` | `ProductoMes[]` | Lista de `{producto, version, unidad, estado}` presentes en la serie (`estado` es `"final"` o `"provisional"`) |
| `producto_mes` | `number[]` | Arreglo de largo `n_meses` (`323`): índice en `productos` para cada mes `0..322`, o `-1` si ese mes no tiene producto |
| `tipo_rango` | texto | `"espacial"` (`p10` y `p90` representan la dispersión espacial entre celdas válidas dentro de la unidad, nunca incertidumbre del sensor) |
| `valor` | `(number \| null)[][]` | Matriz `len(ids) × n_meses` en la **unidad física del producto** (6 cifras significativas); `null` cuando no hay valor o `frac_valida < 0,5` |
| `p10`, `p90` | `(number \| null)[][]` | Matrices `len(ids) × n_meses` con los percentiles 10 y 90 ponderados entre celdas válidas (5 cifras significativas) |
| `frac` | `(number \| null)[][]` | Matriz `len(ids) × n_meses` con `frac_valida` redondeada a 3 decimales; se conserva aunque `valor` sea `null` por estar bajo el umbral `0,5` |

### 2.1 Unidades físicas por mes y empalme de IMERG (D-023)

Los archivos estáticos guardan el valor en la unidad física original del producto reportada en `productos[producto_mes[mes]].unidad`:

- `precip`: `"mm/hr"` de `2000-01` a `2025-09` (GPM IMERG Final V07B, `estado = "final"`) y `"mm/day"` de `2025-10` a `2026-10` (GPM IMERG Late V07B diario agregado en UTC con umbral de 80 % de días válidos, `estado = "provisional"`).
- `t2m`: `"K"` de `2000-01` a `2026-09` (MERRA-2 `M2TMNXSLV` 5.12.4, `estado = "final"`).
- `sm_raiz`: `"kg m-2"` de `2000-01` a `2026-07` (GLDAS Noah 0,25° mensual 2.1 `RootMoist_inst`, rotulado explícitamente como `MODELO`, `estado = "final"`).
- `ndvi`: `"1"` de `2000-02` a `2026-10` (MODIS Terra `MOD13C2` 061, `estado = "final"`).

La conversión a unidad de pantalla (`mm/mes` con los días UTC reales de cada mes, `°C`, `kg/m²`, `adimensional`) ocurre únicamente en `src/web/src/comun/unidades.ts` (`paraMostrar`). Cualquier par `(variable, unidad)` desconocido lanza excepción y los paneles muestran el estado de error (`unidad.sinConversion`), nunca el número crudo.

## 3. Esquema de `datos/unidades_geo.json.gz` y `datos/lotes_demo.json`

- `datos/unidades_geo.json.gz`: objeto JSON cuyas claves son los `unidad_id` de los niveles 0, 1 y 2 de `unidades.gpkg` (excluyendo filas que solo repiten un nivel superior, `nivel_real != capa`). El valor es `[oeste, sur, este, norte, padre_id]` con coordenadas en grados WGS84 redondeadas a 3 decimales y `padre_id` (`string | null`). Si la caja cruza el antimeridiano (`oeste <= -179.9` y `este >= 179.9`), se añaden `[punto_lon, punto_lat]` en las posiciones 5 y 6 para volar al punto interior sin abrir todo el planisferio.
- `datos/lotes_demo.json`: copia pública de `datos/lotes/lotes_demo.json` (D-027), con `version: 1` y `lotes`:
  - `DEMO-USA-01` (`unidad_id: "USA-ADM2-52423323B480079355264"`, Saunders, Nebraska, EE. UU.)
  - `DEMO-COL-01` (`unidad_id: "COL-ADM2-7082276B52108893597118"`, Ipiales, Nariño, Colombia)

## 4. Esquema de `datos/manifiesto.json` y presupuesto de tamaño medido

`datos/manifiesto.json` registra `version_contrato` (`"web_datos v0"`), `generado_utc`, `paises` (`["COL"]`), `mes0`, `n_meses`, `variables` (con `niveles`, `meses_disponibles: {desde, hasta, n_meses_con_producto}` y `productos`), `total_bytes` y el mapa `archivos` con `bytes` y `sha256` de cada archivo generado (VERIFICADO):

| Archivo | Bytes | Tamaño (KB / MB) | SHA-256 |
|-|-:|-:|-|
| `COL/precip_0.json.gz` | 2.941 | 2,9 KB | `9a7f3ccf721e3e723f2b3b8f02296b20f9333f6ebdcaedcad7cde361f9105c07` |
| `COL/precip_1.json.gz` | 91.462 | 91,5 KB | `8a027f666b66b62a4636b915df52ba5ca364fc2133397fc1146966a6bbc85577` |
| `COL/precip_2.json.gz` | 3.169.684 | 3,17 MB | `af5072bdfb207b2cfa2f4fc00b297ebedb2ff52693f54d8c0d0692d137c66a48` |
| `COL/t2m_0.json.gz` | 2.388 | 2,4 KB | `cf1630ff573f23658c4798f8a529566cb2ff1d8cab74b8a98c67fc2a139c87b0` |
| `COL/t2m_1.json.gz` | 65.054 | 65,1 KB | `35a2d84b9c91d061e3aaa71b5eb6bda517a9525e79c88985aab0f772a4054cf4` |
| `COL/t2m_2.json.gz` | 2.066.514 | 2,07 MB | `0fcb0a6730f4f936b537b8fd3402466dc1210923250fc1a1b4b8329c56236b34` |
| `COL/sm_raiz_0.json.gz` | 3.469 | 3,5 KB | `bb7a21b30899b4cfc3bbe75b01692bd45685c764a5012f12871720d4ea32ae6d` |
| `COL/sm_raiz_1.json.gz` | 92.896 | 92,9 KB | `637d2a66c18d65747c00fee15c32c64bfe401483e74d5d10f5ff48f595727c47` |
| `COL/sm_raiz_2.json.gz` | 3.109.718 | 3,11 MB | `1cd51be2c1111c2a94bd485ffe23df9322ac975351c5a732034af42daeec2dd0` |
| `COL/ndvi_0.json.gz` | 3.207 | 3,2 KB | `81f2200a8ab6919986ee10c18605056386166d2919de1252586d6811df340ca3` |
| `COL/ndvi_1.json.gz` | 95.518 | 95,5 KB | `a0790159ed1418f0fb3a242c98e67509d2a7522b7d6ed0fcc53305e06cba83ba` |
| `COL/ndvi_2.json.gz` | 3.085.802 | 3,09 MB | `8a85f946b57aa9fa6ad8ec3da2affd75c24751dd083bdeae1320ae76feea09d8` |
| `unidades_geo.json.gz` | 1.236.212 | 1,24 MB | `fc7df4d0374381c62abffa74d3b7e47d8483045d6bcc8d6d7660b6eff16c272d` |
| `lotes_demo.json` | 1.510 | 1,5 KB | `b5a815e1e9ebfcc27254fd927d415040379c4d93b5536787387124a021ce5d6a` |
| `meta.json` | 1.717 | 1,7 KB | `2bb5aa2b56ec6ef010141bc4ec5f66262bdb13706e006a5add24d01152cbf2a2` |
| **Total (`total_bytes`)** | **13.028.092** | **13,03 MB** | — |

- Carga inicial de una variable en los 3 niveles para Colombia (`precip_{0,1,2}.json.gz`): **3,26 MB** comprimidos en total (se cachean en memoria en `estatico.ts` al primer pedido).
- `unidades_geo.json.gz` (**1,24 MB**) solo se descarga cuando el usuario selecciona una unidad para volar a su encuadre.
- D-033e: `unidades_geo.json.gz` cubre el mundo y no se versiona; se construye al desplegar con `src/mapa_estatico/construir.py`. Los archivos de `COL/` ya versionados se quedan.
- T-W4: la prueba de alojamiento mide cada `.json.gz` con y sin `Content-Encoding: gzip`; `leerGz` acepta los dos casos (prueba en `estatico.test.ts`, RED con el código viejo en `datos/evidencia/leergz_red.txt`).

## 5. Reglas sobre `SIMULADO` y unidades sin dato real

1. **Variables con dato real (`precip`, `sm_raiz`, `t2m`, `ndvi` en `PAISES_CON_DATO`):** no llevan la etiqueta `SIMULADO` en el globo ni en los paneles (`Resumen`, `Series`, `Fuentes`, `Suelo`, `PanelRegion`), verificado por prueba automática en `src/web/pruebas/estatico.test.ts`.
2. **Unidades fuera de `PAISES_CON_DATO`:** en esta v0 solo `COL` está en `PAISES_CON_DATO`. Cualquier unidad de otro país devuelve `SIN_DATO_REAL` (`{ ok: false, hueco: false }`), no se pinta ni se trama como hueco del sensor, y muestra el texto `"sin dato real todavía"` (`panel.sinDatoReal`).
3. **Huecos reales del producto:** cuando `producto_mes[mes] >= 0` pero `valor` es `null` (por nubosidad en MOD13C2 o `frac_valida < 0,5`), la unidad se marca con `hueco: true` y se dibuja con la trama de `"sin dato del producto"`, conservando `frac_valida` en el panel.
4. **Componentes que siguen simulados:** cualquier vista que aún no lea datos reales conserva explícitamente el rótulo `SIMULADO` hasta que se reemplace o se retire.

## 6. Reproducibilidad y pruebas

- Generación reproducible:
  ```bash
  PYTHONPATH=src python -m mapa_estatico.construir \
    --series C:/NASA/AGROVERSEx/datos/procesados/series/COL \
    --gpkg C:/NASA/AGROVERSEx/datos/procesados/unidades.gpkg \
    --lotes datos/lotes/lotes_demo.json \
    --salida src/web/public/datos \
    --pais COL \
    --generado-utc 2026-11-14T22:50:00Z
  ```
- Despliegue del build público (D-037 C2.2, D-040; director 10:00): después de `npm run build` en `src/web`,
  ```bash
  AGROVERSEX_DATOS=C:/NASA/AGROVERSEx/datos/procesados \
  AGROVERSEX_TESELAS=C:/NASA/teselas_publicas \
  PYTHONPATH=src python -m mapa_estatico.construir --desplegar src/web/dist
  ```
  copia a `dist/teselas/` los `adm0/1/2.pmtiles` y el índice de búsqueda, y construye `dist/datos/unidades_geo.json.gz`.
  - `AGROVERSEX_DATOS` es obligatoria: carpeta con `teselas/`, `indice_busqueda.json.gz` y `unidades.gpkg`. Si falta, o falta o está vacío un archivo, el paso termina con `ERROR de despliegue: ...`.
  - `AGROVERSEX_TESELAS`: carpeta con las copias limpias de los `.pmtiles` (metadatos sin rutas internas; teselas idénticas byte a byte). Si está definida, los `.pmtiles` salen de ahí en vez de `AGROVERSEX_DATOS/teselas/`.
  - Al terminar se revisa todo `dist` (texto, `.gz` y metadatos de `.pmtiles`): si aparece una ruta local (`/home/`, `/Users/`, `\Users\`, `C:\`) o el usuario de la máquina como segmento de ruta, el despliegue falla. Con las teselas originales falla; con las copias limpias pasa.
  - Las mismas teselas limpias se publican en el repo público `Daniel-JP10/agroversex-teselas` (GitHub Pages, D-040); la app aún no las lee de ahí.
- Pruebas automáticas:
  - `pytest pruebas/mapa/test_construir.py` (7/7 en verde)
  - `npx vitest run pruebas/estatico.test.ts` (16/16 en verde, incluida la verificación de SHA-256 de los 15 archivos de `manifiesto.json`)
