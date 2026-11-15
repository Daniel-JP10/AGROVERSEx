# Licencias de terceros · Área Gemelo

Registro exigido por los términos de Space Apps 2026 y `AGENTS.md §5.1`. Incluye todas las fuentes de datos, modelos externos y librerías Python fijadas en `requirements-gemelo.txt` y `requirements-gemelo.lock.txt`.

Ninguna fuente de datos ni librería de terceros involucra entidades afiliadas o de propiedad de China (incluidos Hong Kong y Macao).

## Datasets y referencias externas

| Producto | Versión | Licencia | Enlace a la licencia | Cómo se cita | Quién lo agregó | Fecha | Estado |
|-|-|-|-|-|-|-|-|
| NASA POWER (Langley Research Center), series diarias comunidad AG | API POWER diaria (`2001-2024` y `2005-2024`) | Guía de uso de datos abiertos de NASA Earthdata: CC0 salvo restricción marcada (INFERENCIA de aplicación general sobre páginas de Earthdata para POWER) | https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | *"The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division."* + servicio, versión y fecha de acceso (`https://power.larc.nasa.gov/docs/referencing/`) | Antigravity (relevo Gemelo), contrastado con Datos | 2026-11-14 | VERIFICADO (política Earthdata y texto oficial de cita leídos) |
| SoilGrids 2.0 (ISRIC World Soil Information) | 2.0 (REST v2.0) | CC BY 4.0 | https://www.isric.org/explore/soilgrids/faq-soilgrids | Poggio, L., de Sousa, L. M., Batjes, N. H., Heuvelink, G. B. M., Kempen, B., Ribeiro, E., & Rossiter, D. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. *SOIL*, 7, 217–240. https://doi.org/10.5194/soil-7-217-2021 | Antigravity (relevo Gemelo), contrastado con Datos | 2026-11-14 | VERIFICADO (`CC BY 4.0` y DOI oficial en `soil-7-217-2021`) |
| Índice ONI / RONI, NOAA CPC (ERSST.v6) | ERSST.v6 | Dominio público (aviso NWS: *"in the public domain, unless specifically noted otherwise"*) | https://www.weather.gov/disclaimer | NOAA Climate Prediction Center ONI/RONI (`origin/datos:src/simulacion/referencias/enso.yaml`, `INV-CLI §1.3–§1.4`, `EV-CLI-002`; formato de cita formal de CPC PENDIENTE) | Cursor / Antigravity (copiado de `origin/datos`) | 2026-11-14 | FUENTE |
| Extractos de referencia internos de Mead y Ames (`datos/referencia/clima/power_*_diario.csv`, `datos/referencia/suelo/soilgrids_*.json`) | N/A (extractos internos) | Mismas licencias de origen: NASA POWER y SoilGrids 2.0 (`CC BY 4.0`) | Ver filas de NASA POWER y SoilGrids 2.0 | Mismas citas de NASA POWER y Poggio et al. (2021) | Antigravity (auditado por D-029) | 2026-11-14 | VERIFICADO (inspección directa de cabeceras; uso solo como fijación interna de pruebas por D-029, nunca en la app) |

## Librerías Python (`requirements-gemelo.lock.txt`)

Todas las versiones y licencias se verificaron directamente en los metadatos instalados en `.venv` (Python 3.12.4) y en el árbol de bloqueos con hashes SHA-256 (`requirements-gemelo.lock.txt`).

### Dependencias directas (`requirements-gemelo.txt`)

| Librería | Versión | Licencia | Enlace oficial | Cómo se cita | Quién lo agregó | Fecha | Estado |
|-|-|-|-|-|-|-|-|
| `numpy` | 1.26.4 | BSD-3-Clause (`Copyright (c) 2005-2023, NumPy Developers`) | https://numpy.org | No requiere cita obligatoria de software en entrega técnica | Cursor / Antigravity | 2026-11-14 | VERIFICADO |
| `pandas` | 2.2.3 | BSD-3-Clause | https://pandas.pydata.org | No requiere cita obligatoria de software en entrega técnica | Cursor / Antigravity | 2026-11-14 | VERIFICADO |
| `PyYAML` | 6.0.3 | MIT | https://pyyaml.org/ | No requiere cita | Cursor / Antigravity | 2026-11-14 | VERIFICADO |
| `scipy` | 1.17.1 | BSD-3-Clause (`Copyright (c) 2001-2002 Enthought, Inc. 2003, SciPy Developers`) | https://scipy.org/ | No requiere cita obligatoria de software en entrega técnica | Cursor / Antigravity | 2026-11-14 | VERIFICADO |
| `pymoo` | 0.6.2 | Apache-2.0 (`Apache License, Version 2.0`) | https://pymoo.org | Blank, J., & Deb, K. (2020). pymoo: Multi-Objective Optimization in Python. *IEEE Access*, 8, 89497–89509. https://doi.org/10.1109/ACCESS.2020.2990567 | Cursor / Antigravity | 2026-11-14 | VERIFICADO (archivo `LICENSE` y metadatos en `.venv`) |
| `pytest` | 9.1.1 | MIT | https://docs.pytest.org/en/stable/ | No requiere cita (solo pruebas) | Cursor / Antigravity | 2026-11-14 | VERIFICADO |
| `matplotlib` | 3.11.2 | PSF-based (`License agreement for matplotlib versions 1.3.0 and later`) | https://matplotlib.org | No requiere cita obligatoria (diagnóstico visual auxiliar) | Cursor / Antigravity | 2026-11-14 | VERIFICADO |

### Dependencias transitivas bloqueadas en `requirements-gemelo.lock.txt`

| Librería | Versión | Licencia | Vía | Enlace | Estado |
|-|-|-|-|-|-|
| `about-time` | 4.2.1 | MIT | `alive-progress` | https://github.com/rsalmei/about-time | VERIFICADO |
| `alive-progress` | 3.3.0 | MIT | `pymoo` | https://github.com/rsalmei/alive-progress | VERIFICADO |
| `autograd` | 1.9.1 | MIT | `pymoo` | https://github.com/HIPS/autograd | VERIFICADO |
| `cffi` | 2.1.1 | MIT-0 | `moocore` | https://cffi.readthedocs.io/ | VERIFICADO |
| `cma` | 4.5.0 | BSD-3-Clause | `pymoo` | https://github.com/CMA-ES/pycma | VERIFICADO |
| `colorama` | 0.4.6 | BSD-3-Clause | `pytest` | https://github.com/tartley/colorama | VERIFICADO |
| `contourpy` | 1.3.3 | BSD-3-Clause | `matplotlib` | https://github.com/contourpy/contourpy | VERIFICADO |
| `cycler` | 0.12.1 | BSD-3-Clause | `matplotlib` | https://matplotlib.org/cycler/ | VERIFICADO |
| `Deprecated` | 3.0.1 | MIT | `pymoo` | https://github.com/laurent-laporte-pro/deprecated | VERIFICADO |
| `fonttools` | 4.68.0 | MIT | `matplotlib` | https://github.com/fonttools/fonttools | VERIFICADO |
| `graphemeu` | 0.7.2 | MIT | `alive-progress` | https://github.com/timendum/grapheme | VERIFICADO |
| `iniconfig` | 2.3.1 | MIT | `pytest` | https://github.com/pytest-dev/iniconfig | VERIFICADO |
| `kiwisolver` | 1.5.1 | BSD-3-Clause (Modified BSD) | `matplotlib` | https://github.com/nucleic/kiwi | VERIFICADO |
| `moocore` | 0.3.2 | LGPL-2.1-or-later | `pymoo` | https://multi-objective.github.io/moocore/python/ | VERIFICADO y aprobada por Daniel (chat 17:10, **D-028**) |
| `packaging` | 26.3 | Apache-2.0 OR BSD-2-Clause | `matplotlib`, `pytest` | https://packaging.pypa.io/ | VERIFICADO |
| `pillow` | 13.0.0 | MIT-CMU | `matplotlib` | https://python-pillow.org/ | VERIFICADO |
| `platformdirs` | 4.14.5 | MIT | `moocore` | https://github.com/platformdirs/platformdirs | VERIFICADO |
| `pluggy` | 1.7.0 | MIT | `pytest` | https://github.com/pytest-dev/pluggy | VERIFICADO |
| `pycparser` | 3.12 | BSD-3-Clause | `cffi` | https://github.com/eliben/pycparser | VERIFICADO |
| `Pygments` | 2.21.0 | BSD-2-Clause | `pytest` | https://pygments.org | VERIFICADO |
| `pyparsing` | 3.3.3 | MIT | `matplotlib` | https://github.com/pyparsing/pyparsing | VERIFICADO |
| `python-dateutil` | 4.0.0 | BSD-3-Clause | `matplotlib`, `pandas` | https://github.com/dateutil/dateutil | VERIFICADO |
| `pytz` | 2026.6 | MIT | `pandas` | https://pythonhosted.org/pytz | VERIFICADO |
| `tzdata` | 2026.6 | Apache-2.0 | `pandas` | https://github.com/python/tzdata | VERIFICADO |
| `wrapt` | 2.5.2 | BSD-2-Clause | `Deprecated` | https://github.com/GrahamDumpleton/wrapt | VERIFICADO |
| GPM IMERG Final Run daily V07 (GPM_3IMERGDF.07), lectura OPeNDAP de una celda por lote | 07 (archivos V07B) | Guía de uso y cita de EOSDIS, igual que las filas de IMERG anteriores: CC0 salvo restricción marcada | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Huffman et al. (2023), GPM IMERG Final Precipitation L3 1 day 0.1 degree x 0.1 degree V07, https://doi.org/10.5067/GPM/IMERGDF/DAY/07 | Claude Code / Antigravity (constructor T-D5) | 2026-11-14 | VERIFICADO (CMR y doi.org) |
| GHCN-Daily (NOAA NCEI), estación `COM00080370` (Aeropuerto San Luis, Ipiales; validación de temperatura y lluvia en `DEMO-COL-01`) y referencia `USC00255362` | v3.31+ (acceso diario CSV por estación) | Dominio público de EE. UU. (17 U.S.C. § 105; datos de NOAA NCEI sin restricción de uso ni redistribución, exigiendo citar la fuente) | https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt y https://www.weather.gov/disclaimer | Menne, M. J. et al. (2012), J. Atmos. Oceanic Technol. 29:897-910, https://doi.org/10.1175/JTECH-D-11-00103.1; dataset https://doi.org/10.7289/V5D21VHZ | Antigravity (constructor T-D5, Prioridad 3A) | 2026-11-14 | VERIFICADO |
