# Ficha de dataset

- Nombre corto: imerg_late
- Producto oficial y versión: GPM IMERG Late Run diario, GPM_3IMERGDL versión 07 (V07C). Colección C2723754859-GES_DISC. No existe Late mensual en CMR. VERIFICADO
- Agencia y centro de datos: NASA, GES DISC
- Página oficial: PENDIENTE; https://cmr.earthdata.nasa.gov/search/concepts/C2723754859-GES_DISC.umm_json
- DOI: 10.5067/GPM/IMERGDL/DAY/07. Cita: Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., Tan, J., & Editor: Savtchenko A. (2023). GPM IMERG Late Precipitation L3 1 day 0.1 degree x 0.1 degree V07 [Dataset]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/GPM/IMERGDL/DAY/07 Colección C2723754859-GES_DISC. Licencia (use_constraints de CMR, textual): The Earth Observing System Data and Information System (EOSDIS) data use and citation guidance for NASA data can be accessed at https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance. For information on how to properly cite and acknowledge data from the NASA GES DISC, refer to https://disc.gsfc.nasa.gov/data-guidelines.. VERIFICADO (CMR y doi.org coinciden; `Docu/datos/citas_cmr.json`). GPM es una misión conjunta de NASA y JAXA, socia de Space Apps.
- Variable y unidades: `precipitation` y `randomError` en **mm/day** según CMR (fill -9999.9), más `precipitation_cnt` y `precipitation_cnt_cond`. OJO: el mensual Final está en mm/hr y el diario Late en mm/day; se conserva la unidad del producto y la agregación a mes debe declarar la conversión. Valores no leídos
- Resolución espacial nominal: 0,1 grados
- Resolución temporal: diaria (UTC, granulo de 00:00:00 a 23:59:59)
- CRS nativo: PENDIENTE
- Periodo descargado: Descargado: 2025-10-01 a 2026-11-13, 409 archivos, 7,779 GB
- Área descargada: global previsto
- Herramienta y consulta exacta de descarga: `python -m simulacion.geo.descargas_nasa imerg_late 6`; consulta por granulo en `datos/manifiesto_imerg_late.yaml`, hashes en `datos/hashes_imerg_late.jsonl`. Forma: `earthaccess.search_data(short_name='GPM_3IMERGDL', version='07', temporal=('2025-10-01', None))` con subconjunto de `precipitation` y `randomError`. Último granulo en CMR: `GPM_3IMERGDL.07:3B-DAY-L.MS.MRG.3IMERG.20261113-S000000-E235959.V07C.nc4`
- Fecha de descarga: 2026-11-14, 13:29 a 13:55 hora de Colombia
- Banderas de calidad aplicadas: PENDIENTE
- Fracción de datos válidos en el área: Valores revisados en el granulo 2025-10-01: `precipitation` float32 mm/day, relleno -9999.9004, rango 0 a 454,9 mm/día, 99,9 % válido; `randomError` mm/day con máximo 218369 (valor absurdo, descartar o tratar como atípico, PENDIENTE). Arreglo (lon, lat) crecientes. En Colombia, los 13 meses completos 2025-10 a 2026-10 tienen todos los días válidos en todas las celdas: la regla del 80 % no excluye nada ahí (ver `T-D3_descargas.md`). Meses sin completar: 2026-11 (13 de 30 días) sale NaN. VERIFICADO
- Transformaciones a la grilla común y método de remuestreo: diario a mensual en UTC, promedio de los días válidos (mm/día, unidad del producto sin convertir). Regla D-011: una celda-mes es válida si tiene al menos el 80 % de los días del CALENDARIO con dato (24 de 30, 25 de 31, 23 de 28); se aplica por celda antes de agregar a la unidad; por debajo queda NaN con motivo `dias_validos_insuficientes`, y un mes en curso (menos granulos que días) sale NaN. Una unidad-mes es NaN si ninguna celda que la toca es válida. SUPUESTO, sin literatura; revisión 2026-11-15 08:00 con la sensibilidad 70/80/90 de `Docu/datos/T-D3_descargas.md`. Código: `src/simulacion/geo/imerg_late.py` (prueba `pruebas/geo/test_imerg_late.py`)
- Limitaciones conocidas: Provisional: Late se reemplaza por Final cuando exista; el mes en curso no se agrega. Revisado un granulo con valores reales (ver Fracción de datos válidos)
- Requisito del reto y pregunta que atiende: N2, D1, D2, F4; PI-D1 y PI-D4. Compuerta G2
- Responsable: constructor de datos (subagente), orquestador de datos Daniel
- Verificador y fecha: PENDIENTE


## Revisión de `randomError` (T-D2, 2026-11-14)

- Lectura descartada como causa: en el DMR de GPM_3IMERGDL 07 la variable `randomError` trae `units` mm/day, `_FillValue` -9999,900391 y ningún `scale_factor`, `add_offset` ni `missing_value`. El relleno se enmascara (0 celdas con relleno en `randomError` en tres días revisados, 2025-10-01, 2026-04-23 y 2026-11-13) y no hay escala que aplicar.
- Distribución (2025-10-01): mediana 3,1 mm/día, percentil 90 de 461, percentil 99 de 4.802 y máximo 218.369; 372 mil celdas por encima de 1.000. En el 100 % de las celdas con precipitación mayor que 1 mm/día el error es mayor que la propia precipitación (máximo: precipitación 403 mm/día y error 218.369, unas 540 veces). Tres días de tres meses distintos dan el mismo patrón.
- Conclusión (INFERENCIA, no corregida): la lectura es correcta y los valores no se pueden interpretar como un error cuadrático medio en mm/día. `randomError` de Late NO se usa como rango. Todo rango de lluvia es `tipo_rango = espacial`. Queda como PENDIENTE preguntar a GES DISC por la unidad real o el significado de `randomError` en el producto diario Late.
- Orientación: igual que Final (ver `imerg_final.md`), el arreglo de GDAL sale espejado en longitud; `lectura_nasa.py` lo corrige y lo comprueba con puntos de control.
