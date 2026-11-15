# Fracción de observaciones HLS v2.0 válidas por píxel y mes (T-D5 Parte B)

Fuente: `datos/procesados/lotes/<lote>/hls_validez.json`, HLSL30 y HLSS30 v2.0, Fmask, 2022-01 a 2024-12. Válida = con dato y sin nube, adyacente a nube/sombra, sombra ni nieve. Cada celda: media de los píxeles del lote de la fracción válida del mes; entre paréntesis, escenas del mes. Rótulo: VERIFICADO por ejecución propia, pendiente de revisión por otra persona.

DEMO-COL-01: 930 píxeles en la ventana, 564 gránulos, fallos de lectura 0.
DEMO-USA-01: 930 píxeles en la ventana, 466 gránulos, fallos de lectura 0.

| Mes | COL media (escenas) | COL q05-q95 píxeles | USA media (escenas) | USA q05-q95 píxeles |
|-|-|-|-|-|
| 01 | 0.13 (52) | 0.12-0.14 | 0.15 (33) | 0.13-0.19 |
| 02 | 0.04 (38) | 0.00-0.13 | 0.59 (42) | 0.54-0.63 |
| 03 | 0.12 (40) | 0.06-0.19 | 0.57 (28) | 0.54-0.62 |
| 04 | 0.07 (40) | 0.00-0.15 | 0.69 (39) | 0.69-0.69 |
| 05 | 0.04 (48) | 0.04-0.04 | 0.60 (39) | 0.55-0.66 |
| 06 | 0.03 (45) | 0.00-0.06 | 0.53 (41) | 0.44-0.58 |
| 07 | 0.02 (48) | 0.00-0.04 | 0.66 (44) | 0.57-0.73 |
| 08 | 0.11 (55) | 0.04-0.18 | 0.62 (40) | 0.60-0.70 |
| 09 | 0.16 (52) | 0.07-0.25 | 0.64 (46) | 0.62-0.67 |
| 10 | 0.09 (53) | 0.06-0.15 | 0.80 (45) | 0.76-0.85 |
| 11 | 0.13 (46) | 0.07-0.20 | 0.54 (39) | 0.49-0.57 |
| 12 | 0.14 (47) | 0.11-0.17 | 0.46 (30) | 0.41-0.51 |

DEMO-COL-01: media de los 36 meses 0.09; mín 0.00, máx 0.27; mediana 0.07; meses con fracción media < 0,25: 33; escenas por mes: mediana 16, mín 6.
DEMO-USA-01: media de los 36 meses 0.57; mín 0.02, máx 0.93; mediana 0.59; meses con fracción media < 0,25: 3; escenas por mes: mediana 13, mín 8.
