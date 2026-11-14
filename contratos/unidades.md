# Contrato de unidades · v0 (2026-11-14, T-D1)

Estado: v0, provisional en conteos y listas; el formato de `unidad_id` y los atributos son lo que Web puede usar ya. Los conteos y la lista de países sin nivel 2 se regeneran de los datos al cerrar T-D1 (v1). Decisión de origen: D-002.

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
| `padre_id` | texto o nulo | `unidad_id` de la unidad del nivel superior que contiene el punto interior. Nulo solo en nivel 0 |
| `nombre` | texto | `shapeName` de CGAZ; puede faltar en 37 unidades de ADM2 (se rellena con el `unidad_id`) |
| `area_km2` | real | Área en km² calculada en proyección de igual área ESRI:54009 (Mollweide) |
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

Reales (22): AND, ARE, ATA, ATG, BHR, BRB, DMA, ESH, GRD, GRL, KNA, LBY, LIE, MDA, MHL, MLT, MNE, MUS, NRU, SMR, TTO, VAT, VCT. Más las 19 zonas en disputa numéricas (111 a 129). En esos países la capa ADM2 repite la geometría de nivel 1 (o de nivel 0 para ATA y VAT): Web no debe mostrar "municipio". Lista de v0 obtenida con una consulta a la tabla; la lista final se regenera en `datos/procesados` y reemplaza esta.

## Avisos para Web

- Los límites son ilustrativos. Las zonas en disputa siguen el criterio de CGAZ (Departamento de Estado de EE. UU.); el aviso se mantiene.
- `maxzoom` de cada capa con un nivel de margen sobre el zoom visible, apagando por opacidad: MapLibre filtra por el zoom entero de la tesela.
- Los ids de GADM del prototipo no existen en este repo.
