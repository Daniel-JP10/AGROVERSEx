# Contrato de unidades · v0 (2026-11-14, T-D1)

Estado: v0 con conteos y listas derivados de los datos construidos el 2026-11-14 (`unidades_informe.json`); el formato de `unidad_id` y los atributos son lo que Web puede usar ya. Decisión de origen: D-002.

## Fuente

geoBoundaries CGAZ, ADM0, ADM1 y ADM2, archivos `geoBoundariesCGAZ_ADM{0,1,2}.gpkg` del repositorio oficial `wmgeolab/geoBoundaries`, ruta `releaseData/CGAZ/`, commit `4004e96433a2bdc54cac2b88d7d2e694c89cb818` (2024-04-20). Línea de versión publicada: geoBoundaries 6.0.0 (2023-09-14). Licencia CC BY 4.0, cita Runfola et al. (2020), PLoS ONE 15(4): e0231866, https://doi.org/10.1371/journal.pone.0231866. Detalle y hashes en `datos/fichas/`.

## Formato de `unidad_id`

Texto, estable mientras no cambie el archivo fuente, único en todo el conjunto (no solo por nivel).

| Nivel | Formato | Ejemplo real |
|-|-|-|
| 0 | `{iso3}-ADM0` | `COL-ADM0` |
| 1 | `{iso3}-ADM1-{shapeID}` | `COL-ADM1-13589884B81785725414319` (Nariño) |
| 2 | `{iso3}-ADM2-{shapeID}` | `COL-ADM2-7082276B52108893597118` (Ipiales) |

- `iso3` es el campo `shapeGroup` de CGAZ, en mayúsculas. Kosovo es `XKX`.
- `shapeID` es el campo `shapeID` de CGAZ, sin cambios. CGAZ ADM0 no trae `shapeID`, por eso el nivel 0 usa solo el país.
- Las zonas en disputa de CGAZ (`shapeType = DISP`) conservan su `shapeGroup` como `iso3` (números `111` a `129`, o `ESH`) y llevan `es_disputa = 1`. Ejemplo: `111-ADM0` (Abyei), `ESH-ADM0`.
- Las unidades de nivel 1 y 2 no son filas de CGAZ de otro nivel: un país sin nivel 2 trae en la capa ADM2 su polígono de nivel 1 y se marca con `nivel_real`.

## Atributos por unidad

| Campo | Tipo | Significado |
|-|-|-|
| `unidad_id` | texto | Ver arriba |
| `nivel` | entero 0, 1 o 2 | Capa de CGAZ de la que sale |
| `nivel_real` | texto | `shapeType` de CGAZ: `ADM0`, `ADM1`, `ADM2` o `DISP`. Si `nivel_real` es menor que `nivel`, la unidad repite un nivel superior (sin municipios en ese país) |
| `iso3` | texto | País (`shapeGroup`) |
| `padre_id` | texto o nulo (`cruce_ambiguo` marca los que el punto interior no resolvió) | `unidad_id` de la unidad del nivel superior que contiene el punto interior. Nulo solo en nivel 0 |
| `nombre` | texto | `shapeName` de CGAZ; falta en 37 unidades de ADM2 y se escribe "Sin nombre {shapeID}" |
| `area_km2` | real | Área en km² calculada en EPSG:6933 (igual área sobre el elipsoide WGS84), con vértices cada 0,1 grados como máximo. Frente al área geodésica del elipsoide: desviación máxima 0,33 % y 99,996 % de las unidades dentro de 0,1 % |
| `es_disputa` | 0 o 1 | Zona en disputa según CGAZ |
| `fuente` | texto | Archivo de origen y versión |

Las teselas llevan solo `unidad_id`, `nombre`, `nivel`, `iso3` y `padre_id`. Web usa `unidad_id` como `promoteId`.

## Conteo por nivel (v0, leído de los archivos)

| Nivel | Unidades | De ellas, disputa |
|-|-|-|
| 0 | 218 | 20 |
| 1 | 3.224 | 20 |
| 2 | 49.349 | 20 |

## Países sin nivel 2 (derivado de los datos: ningún polígono con `shapeType = ADM2` en la capa ADM2)

Son 42 unidades de país o zona. Códigos de país (23): AND, ARE, ATA, ATG, BHR, BRB, DMA, ESH, GRD, GRL, KNA, LBY, LIE, MDA, MHL, MLT, MNE, MUS, NRU, SMR, TTO, VAT, VCT. Códigos de zona en disputa (19): 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129. En todos la capa ADM2 repite la geometría de nivel 1 (o de nivel 0 en ATA y VAT; `nivel_real` lo dice): Web no debe mostrar "municipio" ahí. ESH figura aquí como zona en disputa de CGAZ (`es_disputa = 1`). La lista sale de `paises_sin_nivel2` sobre la capa ADM2 y una prueba comprueba que cada código esté en este párrafo; no se escribe a mano.

## Teselas e índice de búsqueda (generados el 2026-11-14)

| Archivo | Capa | Zoom de las teselas | Tamaño | Unidades |
|-|-|-|-|-|
| `adm0.pmtiles` | `adm0` | 0 a 6 | 4,3 MB | 218 (incluye las 20 zonas en disputa) |
| `adm1.pmtiles` | `adm1` | 2 a 9 | 26,3 MB | 3.224 |
| `adm2.pmtiles` | `adm2` | 5 a 12 | 399 MB | 49.349 |

- Propiedades de cada polígono: `unidad_id`, `nombre`, `nivel`, `iso3`, `padre_id` y nada más. Web usa `promoteId: 'unidad_id'`.
- Los ids de las teselas son exactamente los de las unidades de la capa del mismo nivel (prueba con `tippecanoe-decode`).
- `adm2.pmtiles` pesa 399 MB: es demasiado para un alojamiento con tope de 100 MB por archivo. Decisión pendiente del director (opciones en el traspaso).
- `indice_busqueda.json.gz`: lista de `{id, nivel, n, a, ctx}` con `es` y `en` solo en el nivel 0 (nombres de Natural Earth) y `d: 1` en las zonas en disputa. `id` es el `unidad_id`. No incluye las filas de la capa ADM2 que repiten el nivel 1 ni las disputas de ADM1 y ADM2. Es reproducible: dos corridas dan el mismo sha256.

## Avisos para Web

- Los límites son ilustrativos. Las zonas en disputa siguen el criterio de CGAZ (Departamento de Estado de EE. UU.); el aviso se mantiene.
- `maxzoom` de cada capa con un nivel de margen sobre el zoom visible, apagando por opacidad: MapLibre filtra por el zoom entero de la tesela.
- Los ids de GADM del prototipo no existen en este repo.

## Nombres de Colombia que no coinciden con DIVIPOLA (D-018)

Se dejan como vienen en CGAZ, sin corrección a mano. Fuente: `datos/evidencia/T-D1_colombia_divipola.json`.

| Nombre en CGAZ | Nombre en DIVIPOLA | Emparejamiento |
|-|-|-|
| Distrito Especial, Industrial Y Portuario De Barr* | BARRANQUILLA (08001) | por exclusión en el departamento |
| Mompós | SANTA CRUZ DE MOMPOX (13468) | por exclusión en el departamento |
| Ricaurte (Coloso) | COLOSÓ | por nombre, INFERENCIA |
| Tolú Viejo | SAN JOSÉ DE TOLUVIEJO | por nombre, INFERENCIA |
| Mapiripana | NUEVO BELÉN DE BAJIRÁ | sin emparejar: no parece variante de nombre sino territorio distinto, PENDIENTE de revisión |
