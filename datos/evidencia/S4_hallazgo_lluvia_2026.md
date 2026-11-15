# Hallazgo de lluvia de enero y febrero de 2026 (Colombia): contraste en anomalías

Reproduce: `cd C:\NASA\wt\f2-s4-analisis && set PYTHONPATH=src && C:\NASA\AGROVERSEx\.venv\Scripts\python.exe datos/evidencia/S4_hallazgo_lluvia_2026.py`
Salida numérica: `datos/evidencia/S4_hallazgo_lluvia_2026.json` (solo agregados). Fecha de ejecución: 2026-11-15.

Qué se busca y qué decisión toca: saber si la lluvia de 2026-01 y 2026-02 de IMERG Late (2,4 y 2,1 veces su climatología) es un dato creíble antes de mostrarla a un agricultor como "anomalía" o dejarla como "en revisión".

## Método (todo en anomalías, razón a la climatología del mismo mes calendario)

- IMERG: Colombia (COL-ADM0, media ponderada por área de la serie de T-D3). Climatología = IMERG Final V07B mensual 2000-2025 (mm/hr x 24 = mm/day; 26 años, 25 en oct-dic). Late (mm/day) en 2025-10..2026-10. Razón = Late / climatología Final; z con la desviación estándar de Final.
- POWER: parámetro PRECTOTCORR mensual (MERRA-2 con corrección con observaciones, definición de POWER), 91 puntos de 1 grado dentro de Colombia (media simple, SUPUESTO sin ponderar por área). Climatología propia 2000-2025.
- GHCN-Daily de Colombia (NCEI): descargado a `C:\NASA\compartir\ghcn\` (no entra al repo; Resolución 40 de la OMM).
- ENSO: ONI y RONI de NOAA CPC (oni.ascii.txt y RONI.ascii.txt). Regresión lineal de la razón de Jan (con DJF) y Feb (con JFM) sobre el índice, 2000-2025.

## Resultados

| Mes | IMERG Late / clim. Final (razón, z) | POWER / clim. (razón, z) | Puntos POWER con razón > 2 | Unidades ADM1 con razón Late > 2 |
|---|---|---|---|---|
| 2026-01 | 2,39 (z 4,55) | 2,05 (z 2,99) | 56 de 91 (mediana 2,32) | 26 de 33 (mediana 2,93) |
| 2026-02 | 2,11 (z 4,59) | 1,54 (z 1,80) | 19 de 91 (mediana 1,20) | 20 de 33 (mediana 2,25) |

Etiqueta: VERIFICADO como ejecución propia reproducible (comando de arriba); falta la revisión de un verificador distinto del autor para pasar a VERIFICADO según §6.

Contexto de los otros meses (razón Late / razón POWER): oct 1,29; nov 1,31; dic 1,18; ene 1,17; feb 1,37; mar 0,97; abr 0,81; may 0,77; jun 0,86; jul 0,75; ago 0,68. Late se aleja de POWER entre 0,68 y 1,37 en meses sin anomalía llamativa, de modo que la diferencia de ene (1,17) cae dentro de ese rango y la de feb (1,37) es el extremo superior. Late no tiene meses de traslape con Final, así que su sesgo propio frente a Final no se puede medir de forma directa (limitación).

GHCN (VERIFICADO, inventario de NCEI y archivos descargados): ninguna estación de Colombia (27 con PRCP en el inventario; 26 con último año 2025) tiene PRCP después del 2025-08-24. No hay dato de estación en 2025-10..2026-10, y por tanto ninguno en ene ni feb de 2026. El contraste con tierra no es posible con GHCN. Correlación estación-satélite en anomalías 2000-2024 (IMERG Final de la unidad ADM2 que contiene la estación, 16 estaciones con al menos 60 meses): r de Pearson entre 0,41 y 0,90 (mediana 0,70). Esto indica cuánto sigue IMERG Final a la tierra a escala de unidad; no valida Late.

Error de representatividad: la estación es un punto; IMERG Late es un valor medio de celdas de 0,1 grado agregado a una unidad administrativa; POWER es una rejilla de 0,5 x 0,625 grados muestreada cada 1 grado. Los tres no miden el mismo volumen de aire ni de suelo, y por eso se comparan razones a la climatología propia de cada fuente, no mm absolutos (de hecho Late y POWER difieren en mm: 9,5 frente a 6,6 en enero).

ENSO (FUENTE: NOAA CPC): ONI DJF 2026 = -0,39 y JFM 2026 = -0,21; RONI DJF 2026 = -0,91 y JFM 2026 = -0,76. En 2000-2025 la razón de enero correlaciona con el índice con r entre -0,57 y -0,62 (n = 26); con el valor de 2026 la regresión prevé una razón de 1,06 a 1,14 (sd del residuo 0,26 a 0,28). Lo observado, 2,05 (POWER) y 2,39 (Late), queda a unos 3 a 4 desviaciones del residuo por encima de lo previsto. En febrero la correlación es débil (r de -0,16 a -0,45) y la previsión es 1,01 a 1,08. INFERENCIA: ENSO, en su fase débil de La Niña, explica a lo sumo una parte pequeña del exceso.

## Conclusión

1. Enero de 2026: INFERENCIA con dos fuentes que usan datos y métodos distintos (IMERG Late, satélite; POWER, reanálisis corregido): hay un exceso de lluvia real en dirección (razón de 2,05 a 2,39). El tamaño es incierto (de 2,0 a 2,4 veces) y la causa no es ENSO por sí solo. Causa: PENDIENTE.
2. Febrero de 2026: NO CONCLUYENTE en magnitud. POWER ve un exceso moderado (1,54, mediana por punto 1,20) y IMERG Late ve 2,11; Late está en el extremo alto de su diferencia con POWER. Se mantiene "provisional en revisión".
3. Sin estaciones de Colombia en 2026 en GHCN no hay verdad de terreno para ninguno de los dos meses; el siguiente paso con valor es una fuente de tierra distinta (estaciones del IDEAM, que ni GHCN ni este análisis cubren) o IMERG Final cuando exista (CMR del 2026-11-15: GPM_3IMERGM v07 termina en 2025-09, VERIFICADO).

Limitaciones: Late sin traslape con Final; POWER PRECTOTCORR no es independiente de las estaciones del mundo (su corrección usa observaciones) y no se verificó aquí cuáles; promedio de POWER sin ponderar por área; la razón del bitácora de Datos (3,81 y 3,03) usaba otro agregado que el ADM0 de aquí (2,39 y 2,11): razón de medias frente a mediana de razones por unidad (ADM1: 2,93 y 2,25). Ninguna cifra de este archivo debe ir a un pitch sin la revisión del verificador.

Hallazgo lateral (fuera del encargo, A3): los archivos de Late de 2026-03-03 en adelante son V07C (`crudos/imerg_late/`) y los anteriores V07B, mientras que la serie y la ficha rotulan "07B" para todos los meses.
