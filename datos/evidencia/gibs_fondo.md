<!-- asistido por SI: Claude Code, ficha de evidencia del fondo GIBS -->
# Fondo del globo con NASA GIBS (reemplaza EOX cloudless, D-006)

Consultado 2026-11-14 ~15:16.

## Capas y teselas (VERIFICADO por ejecución propia: curl 200 y GetCapabilities)
- GetCapabilities: https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi?SERVICE=WMTS&REQUEST=GetCapabilities (HTTP 200).
- MODIS_Terra_CorrectedReflectance_TrueColor existe; TileMatrixSet GoogleMapsCompatible_Level9 (zoom máximo 9); formato image/jpeg; Time P1D con rangos desde 2000-02-24; el rango 2022-10-23/2025-08-08 incluye 2024-08-01 (fecha elegida, SUPUESTO).
- Plantilla: https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-08-01/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg
- Tesela z3/3/3 de esa plantilla: 200 image/jpeg. Tesela z6/20/18: 200, 15189 bytes.
- BlueMarble_ShadedRelief_Bathymetry (GoogleMapsCompatible_Level8, .jpeg): aparece en GetCapabilities; tesela z3/3/3: 200 image/jpeg.

## Términos y atribución (FUENTE: una página oficial por afirmación)
- https://nasa-gibs.github.io/gibs-api-docs/ , "Data Use Guidance and Acknowledgements": "NASA promotes full and open sharing of data. We ask that users who make use of GIBS in their clients or when referencing it in written or oral presentations to add the following acknowledgment:" y "We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS)."
- https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-information-guidance : "NASA promotes the full and open sharing of all data with the research and applications communities, private industry, academia, and the general public."

## Limitaciones
- PENDIENTE: no se leyó una cláusula de licencia específica por capa; se aplica la política general de Earthdata.
- Imagen diaria de un solo día: puede tener nubes o huecos de franja; zoom máximo 9 (aprox. 250 m), por debajo del detalle de EOX (14).

## Actualización: fondo por defecto = mosaico sin nubes (decisión del director)
- Capa elegida por defecto: BlueMarble_ShadedRelief (VERIFICADO en GetCapabilities 2026-11-14): sin dimensión Time (se pide con `default/default`), TileMatrixSet GoogleMapsCompatible_Level8, image/jpeg. Justificación: render sin nubes, fecha-independiente. BlueMarble_NextGeneration queda como opción (id gibs-bluemarble-ng). DESFASE VERIFICADO en captura: en Nariño z7.5 se ven manchas blancas (restos de nubes del compuesto Blue Marble) con NextGeneration y con ShadedRelief; son pocas y no franjas de un día, pero el mosaico no está 100% libre de nubes en la cordillera.
- Zoom máximo NATIVO: 8. Prueba: tesela z8/100/80 responde 200 image/jpeg; z9/200/160 responde 400 (BlueMarble_NextGeneration, igual Level8; ver salida de curl del PR).
- Sobrezoom: la fuente MapLibre declara maxzoom 8 (igual al nativo); el mapa sigue ampliando reutilizando teselas z8, sin pedir z9 o más.
- MODIS Terra de un día (nativo 9, 2024-08-01) queda solo como opción (id gibs-modis-terra).
- Limitación: sobre zoom 8 la imagen se ve pixelada (INFERENCIA por el nivel de la matriz).

## Año del mosaico (FUENTE: catálogo oficial de GIBS)
- https://gibs.earthdata.nasa.gov/layer-metadata/v1.0/BlueMarble_ShadedRelief.json : "Blue Marble (August 2004, Shaded Relief)", subtítulo "MODIS / NASA Earth Observatory", "ongoing": false.
- https://gibs.earthdata.nasa.gov/layer-metadata/v1.0/BlueMarble_ShadedRelief_Bathymetry.json : "Blue Marble (August 2004, Shaded Relief and Bathymetry)".
- https://gibs.earthdata.nasa.gov/layer-metadata/v1.0/BlueMarble_NextGeneration.json : "Blue Marble (August 2004)".
- Worldview (https://raw.githubusercontent.com/nasa-gibs/worldview/main/config/default/common/config/metadata/layers/modis/BlueMarble.md): "The MODIS Blue Marble, Next Generation is a static product created with data from 2004 from the MODIS instrument on board the Terra satellite. The image resolution is 500 m."
- Los títulos dicen agosto de 2004 para las tres capas; el GetCapabilities no trae el año. Que ShadedRelief use el mismo compuesto de agosto es lo que dice el título; la descripción de resolución solo aparece para NextGeneration (PENDIENTE para las otras dos).
- Los restos de nubes en los Andes se aceptan como limitación declarada (director). El texto visible está en la clave `fuentes.fondo` (es/en).

## JSON literal de cada capa (curl a https://gibs.earthdata.nasa.gov/layer-metadata/v1.0/<capa>.json, 2026-11-14; está en varias líneas, buscar `"title"`)

```json
// BlueMarble_ShadedRelief
{
  "title": "Blue Marble (August 2004, Shaded Relief)",
  "subtitle": "MODIS / NASA Earth Observatory",
  "ongoing": false,
  "measurement": "Blue Marble",
  "retentionPeriod": -1,
  "daynight": [
    "day"
  ]
}
// BlueMarble_ShadedRelief_Bathymetry
{
  "title": "Blue Marble (August 2004, Shaded Relief and Bathymetry)",
  "subtitle": "MODIS / NASA Earth Observatory",
  "ongoing": false,
  "measurement": "Blue Marble",
  "retentionPeriod": -1,
  "daynight": [
    "day"
  ]
}
// BlueMarble_NextGeneration
{
  "title": "Blue Marble (August 2004)",
  "subtitle": "MODIS / NASA Earth Observatory",
  "ongoing": false,
  "measurement": "Blue Marble",
  "retentionPeriod": -1,
  "daynight": [
    "day"
  ]
}
```
