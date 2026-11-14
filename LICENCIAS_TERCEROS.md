# Licencias de terceros

Todo dataset, librería, herramienta o modelo que no es del equipo, con su licencia. Exigido por los términos de Space Apps 2026 y AGENTS.md §5.1. Las filas en PENDIENTE no se usan en el producto hasta confirmarse.

## Datasets

| Producto | Versión | Licencia | Enlace a la licencia | Cómo se cita | Quién lo agregó | Fecha | Estado |
|-|-|-|-|-|-|-|-|
| geoBoundaries CGAZ (niveles 0 a 2) | Archivos del commit 4004e96 (2024-04-20), línea 6.0.0 | CC BY 4.0 según geoboundaries.org y el LICENSE del repositorio; el archivo no trae licencia. Herencia de las licencias de origen (ODbL, CC BY-SA en parte de los países) sin resolver | https://github.com/wmgeolab/geoBoundaries/blob/main/LICENSE | Runfola et al. (2020), PLoS ONE 15(4): e0231866, https://doi.org/10.1371/journal.pone.0231866 | Claude Code (T-D1), por Daniel | 2026-11-14 | FUENTE; uso público condicionado a la decisión del director sobre la herencia |
| Natural Earth 1:10m (land, ocean, lakes, coastline, admin_0_countries) | 5.1.1, 5.1.1, 5.0.0, 5.0.0-pre9, 5.1.1 (del `.VERSION.txt` de cada zip) | Dominio público | https://www.naturalearthdata.com/about/terms-of-use/ | "Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com." (opcional) | Claude Code (T-D1), por Daniel | 2026-11-14 | FUENTE |
| DIVIPOLA, códigos de municipios (DANE, datos.gov.co gdxc-w37w) | Corte 30 de diciembre de 2024 | CC BY-SA 4.0 según los metadatos de datos.gov.co; solo se usa para comparar, no se redistribuye | https://www.datos.gov.co/d/gdxc-w37w | DANE. DIVIPOLA - Códigos municipios, corte 30 de diciembre de 2024. datos.gov.co | Claude Code (T-D1), por Daniel | 2026-11-14 | FUENTE |
| SoilGrids 2.0, ISRIC | PENDIENTE (T-D4) | CC BY 4.0 según código del prototipo | PENDIENTE | PENDIENTE | Daniel (orquestador de datos) | 2026-11-14 | PENDIENTE |
| Productos NASA (IMERG, MERRA-2 o POWER, SMAP, MODIS o VIIRS, GRACE, SRTM o NASADEM, ECOSTRESS, HLS) | PENDIENTE (T-D3, T-D4, T-D5) | PENDIENTE | PENDIENTE | PENDIENTE | Daniel (orquestador de datos) | 2026-11-14 | PENDIENTE |
| MODIS/Terra Vegetation Indices Monthly L3 Global 0.05Deg CMG V061 (MOD13C2) | 061 | Política de uso de datos de NASA Earthdata (UseConstraints de CMR: https://earthdata.nasa.gov/earth-observation-data/data-use-policy); CC0 salvo restricción marcada según https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Didan, K. (2021). MODIS/Terra Vegetation Indices Monthly L3 Global 0.05Deg CMG V061 [Dataset]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/MODIS/MOD13C2.061 | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| GPM IMERG Final Precipitation L3 1 month 0.1 degree x 0.1 degree V07 (GPM_3IMERGM) | 07 | Guía de uso y cita de EOSDIS (UseConstraints de CMR remite a https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance): CC0 salvo restricción marcada; GPM es misión conjunta NASA y JAXA, socia de Space Apps | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., & Tan, J. (2023). GPM IMERG Final Precipitation L3 1 month 0.1 degree x 0.1 degree V07 [Dataset]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07 | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| GPM IMERG Late Precipitation L3 1 day 0.1 degree x 0.1 degree V07 (GPM_3IMERGDL) | 07 | Guía de uso y cita de EOSDIS (UseConstraints de CMR remite a https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance): CC0 salvo restricción marcada; GPM es misión conjunta NASA y JAXA, socia de Space Apps | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., Tan, J., & Editor: Savtchenko A. (2023). GPM IMERG Late Precipitation L3 1 day 0.1 degree x 0.1 degree V07 [Dataset]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/GPM/IMERGDL/DAY/07 | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| MERRA-2 tavgM_2d_slv_Nx: 2d,Monthly mean,Time-Averaged,Single-Level,Assimilation,Single-Level Diagnostics V5.12.4 (M2TMNXSLV) | 5.12.4 | Guía de uso y cita de EOSDIS (UseConstraints de CMR remite a https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance): CC0 salvo restricción marcada | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Global Modeling and Assimilation Office, & Pawson, S. (2015). MERRA-2 tavgM_2d_slv_Nx: 2d,Monthly mean,Time-Averaged,Single-Level,Assimilation,Single-Level Diagnostics V5.12.4 [Dataset]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/AP1B0BA5PD2K | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| MERRA-2 tavgM_2d_rad_Nx: 2d,Monthly mean,Time-Averaged,Single-Level,Assimilation,Radiation Diagnostics V5.12.4 (M2TMNXRAD) | 5.12.4 | Guía de uso y cita de EOSDIS (UseConstraints de CMR remite a https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance): CC0 salvo restricción marcada | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Global Modeling and Assimilation Office, & Pawson, S. (2015). MERRA-2 tavgM_2d_rad_Nx: 2d,Monthly mean,Time-Averaged,Single-Level,Assimilation,Radiation Diagnostics V5.12.4 [Dataset]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/OU3HJDS973O0 | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| GLDAS Noah Land Surface Model L4 monthly 0.25 x 0.25 degree V2.1 (GLDAS_NOAH025_M) | 2.1 | Guía de uso y cita de EOSDIS (UseConstraints de CMR remite a https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance): CC0 salvo restricción marcada | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Beaudoing, H., Rodell, M., & Hydrological Sciences Laboratory (HSL). (2020). GLDAS Noah Land Surface Model L4 monthly 0.25 x 0.25 degree, Version 2.1 [Dataset]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/SXAVCZFAQLNO | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| SMAP Enhanced L3 Radiometer Global and Polar Grid Daily 9 km EASE-Grid Soil Moisture V006 (SPL3SMP_E) | 006 | UseConstraints.LicenseText de CMR: "These data are freely, openly, and fully available to use without restrictions, provided that you cite the data according to the recommended citation at https://nsidc.org/about/use_copyright.html" | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | ONeill, P., Chan, S., Njoku, E., Jackson, T., Bindlish, R., Chaubell, J., & Colliander, A. (2023). SMAP Enhanced L3 Radiometer Global and Polar Grid Daily 9 km EASE-Grid Soil Moisture, Version 6 [Dataset]. NASA National Snow and Ice Data Center Distributed Active Archive Center. https://doi.org/10.5067/M20OXIZHY3RJ | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and Root Zone Soil Moisture Geophysical Data V008 (SPL4SMGP) | 008 | UseConstraints.LicenseText de CMR: "These data are freely, openly, and fully available to use without restrictions, provided that you cite the data according to the recommended citation at https://nsidc.org/about/use_copyright.html" | https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance | Reichle, R., De Lannoy, G., Koster, R., Crow, W., Kimball, J., Liu, Q., & Bechtold, M. (2025). SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and Root Zone Soil Moisture Geophysical Data, Version 8 [Dataset]. NASA National Snow and Ice Data Center Distributed Active Archive Center. https://doi.org/10.5067/T5RUATAQREF8 | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (CMR) |
| NASA POWER (Langley Research Center), solo contraste (D-012) | PENDIENTE (sale de la respuesta de la API) | Datos de NASA: "Unless the content is marked with a use restriction or license, data provided from a NASA-led mission are licensed as Creative Commons Zero (CC0)"; que cubra a POWER es INFERENCIA, la página no lo nombra | https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance y https://www.earthdata.nasa.gov/engage/open-data-services-and-software/data-and-information-policy (consultadas 2026-11-14 13:28) | Texto de https://power.larc.nasa.gov/docs/referencing/ (ver CITAS.md); POWER pide notificar la redistribución | Daniel (orquestador de datos) | 2026-11-14 | VERIFICADO (texto leído por el investigador y por el orquestador); licencia propia de POWER PENDIENTE |
| Índice ONI, NOAA CPC (ERSST.v6), contexto ENSO | v6 | Dominio público: "in the public domain, unless specifically noted otherwise" (aviso NWS); que cubra al CPC es INFERENCIA | https://www.weather.gov/disclaimer | PENDIENTE (sin formato oficial de cita hallado) | Daniel (orquestador de datos) | 2026-11-14 | FUENTE |

Fuera del proyecto por licencia: GADM (D-002), WorldClim 2.1 (D-004), GAEZ v4 (D-005).

## Librerías Python

Leídas de los metadatos instalados en `.venv` (Windows) y `~/venvs/agroversex_geo` (WSL), desde `requirements-geo.lock.txt` y `requirements-geo-wsl.lock.txt`.

| Librería | Versión | Licencia | Enlace | Cómo se cita | Quién lo agregó | Fecha |
|-|-|-|-|-|-|-|
| affine | 3.0.1 | BSD-3-Clause | https://pypi.org/project/affine/3.0.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| aiobotocore | 3.10.0 | Apache-2.0 | https://pypi.org/project/aiobotocore/3.10.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| aiohappyeyeballs | 2.7.1 | Python Software Foundation License | https://pypi.org/project/aiohappyeyeballs/2.7.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| aiohttp | 3.14.5 | Apache-2.0 AND MIT | https://pypi.org/project/aiohttp/3.14.5/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| aioitertools | 0.13.0 | MIT | https://pypi.org/project/aioitertools/0.13.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| aiosignal | 1.4.0 | Apache Software License | https://pypi.org/project/aiosignal/1.4.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| attrs | 26.1.0 | MIT | https://pypi.org/project/attrs/26.1.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| botocore | 1.43.117 | Apache-2.0 | https://pypi.org/project/botocore/1.43.117/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| bounded-pool-executor | 0.0.3 | MIT License | https://pypi.org/project/bounded-pool-executor/0.0.3/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| certifi | 2026.10.23 | Mozilla Public License 2.0 (MPL 2.0) | https://pypi.org/project/certifi/2026.10.23/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| charset-normalizer | 3.5.2 | MIT | https://pypi.org/project/charset-normalizer/3.5.2/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| click | 8.5.1 | BSD-3-Clause | https://pypi.org/project/click/8.5.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| click-plugins | 1.1.1.2 | BSD License | https://pypi.org/project/click-plugins/1.1.1.2/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| cligj | 0.7.2 | BSD | https://pypi.org/project/cligj/0.7.2/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| colorama | 0.4.6 | BSD License | https://pypi.org/project/colorama/0.4.6/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| earthaccess | 0.19.0 | MIT | https://pypi.org/project/earthaccess/0.19.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| exactextract | 0.3.0 | PENDIENTE | https://pypi.org/project/exactextract/0.3.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| frozenlist | 1.8.0 | Apache-2.0 | https://pypi.org/project/frozenlist/1.8.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| fsspec | 2026.9.0 | BSD-3-Clause | https://pypi.org/project/fsspec/2026.9.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| geopandas | 1.1.4 | BSD-3-Clause | https://pypi.org/project/geopandas/1.1.4/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| idna | 3.20 | BSD-3-Clause | https://pypi.org/project/idna/3.20/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| importlib_resources | 7.1.0 | Apache-2.0 | https://pypi.org/project/importlib_resources/7.1.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| iniconfig | 2.3.1 | MIT | https://pypi.org/project/iniconfig/2.3.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| jmespath | 1.1.0 | MIT License | https://pypi.org/project/jmespath/1.1.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| multidict | 7.2.1 | Apache-2.0 | https://pypi.org/project/multidict/7.2.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| multimethod | 2.1 | Apache-2.0 | https://pypi.org/project/multimethod/2.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| numpy | 1.26.4 | BSD License | https://pypi.org/project/numpy/1.26.4/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | https://pypi.org/project/packaging/26.3/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pandas | 2.2.3 | BSD License | https://pypi.org/project/pandas/2.2.3/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pluggy | 1.7.0 | MIT License | https://pypi.org/project/pluggy/1.7.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pqdm | 0.2.0 | MIT License | https://pypi.org/project/pqdm/0.2.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| propcache | 0.5.4 | Apache-2.0 | https://pypi.org/project/propcache/0.5.4/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| Pygments | 2.21.0 | BSD-2-Clause | https://pypi.org/project/Pygments/2.21.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pyogrio | 0.13.0 | MIT License | https://pypi.org/project/pyogrio/0.13.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pyparsing | 3.3.3 | MIT | https://pypi.org/project/pyparsing/3.3.3/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pyproj | 3.8.0 | MIT | https://pypi.org/project/pyproj/3.8.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pytest | 9.1.1 | MIT | https://pypi.org/project/pytest/9.1.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| python-cmr | 0.13.0 | MIT License | https://pypi.org/project/python-cmr/0.13.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| python-dateutil | 2.9.0.post0 | BSD License; Apache Software License | https://pypi.org/project/python-dateutil/2.9.0.post0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pytz | 2026.6 | MIT License | https://pypi.org/project/pytz/2026.6/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| PyYAML | 6.0.3 | MIT License | https://pypi.org/project/PyYAML/6.0.3/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| rasterio | 1.4.4 | BSD License | https://pypi.org/project/rasterio/1.4.4/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| requests | 2.34.2 | Apache Software License | https://pypi.org/project/requests/2.34.2/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| s3fs | 2026.9.0 | BSD License | https://pypi.org/project/s3fs/2026.9.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| shapely | 2.1.2 | BSD License | https://pypi.org/project/shapely/2.1.2/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| six | 1.17.0 | MIT License | https://pypi.org/project/six/1.17.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| tenacity | 9.2.1 | Apache-2.0 | https://pypi.org/project/tenacity/9.2.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| tinynetrc | 1.3.1 | MIT License | https://pypi.org/project/tinynetrc/1.3.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| tqdm | 4.70.1 | MPL-2.0 AND MIT | https://pypi.org/project/tqdm/4.70.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| typing_extensions | 4.16.0 | PSF-2.0 | https://pypi.org/project/typing_extensions/4.16.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| tzdata | 2026.6 | Apache-2.0 | https://pypi.org/project/tzdata/2026.6/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| urllib3 | 2.8.0 | MIT | https://pypi.org/project/urllib3/2.8.0/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| wrapt | 2.5.2 | BSD-2-Clause | https://pypi.org/project/wrapt/2.5.2/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| yarl | 1.25.1 | Apache-2.0 | https://pypi.org/project/yarl/1.25.1/ | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |

## Paquetes npm

Dependencias directas de `src/web/package.json` y `herramientas/package.json`, leídas de `node_modules/*/package.json`. Las transitivas están en los `package-lock.json`.

| Paquete | Versión | Licencia | Enlace | Cómo se cita | Quién lo agregó | Fecha |
|-|-|-|-|-|-|-|
| @fontsource/ibm-plex-sans | 5.3.0 | OFL-1.1 | https://www.npmjs.com/package/@fontsource/ibm-plex-sans/v/5.3.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| @observablehq/plot | 0.6.17 | ISC | https://www.npmjs.com/package/@observablehq/plot/v/0.6.17 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| @tanstack/react-query | 5.105.0 | MIT | https://www.npmjs.com/package/@tanstack/react-query/v/5.105.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| maplibre-gl | 6.16.0 | BSD-3-Clause | https://www.npmjs.com/package/maplibre-gl/v/6.16.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| minisearch | 7.2.0 | MIT | https://www.npmjs.com/package/minisearch/v/7.2.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pmtiles | 4.5.0 | BSD-3-Clause | https://www.npmjs.com/package/pmtiles/v/4.5.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| react | 19.1.10 | MIT | https://www.npmjs.com/package/react/v/19.1.10 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| react-dom | 19.1.10 | MIT | https://www.npmjs.com/package/react-dom/v/19.1.10 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| zustand | 5.0.16 | MIT | https://www.npmjs.com/package/zustand/v/5.0.16 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| @playwright/test | 1.64.1 | Apache-2.0 | https://www.npmjs.com/package/@playwright/test/v/1.64.1 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| @types/node | 24.19.2 | MIT | https://www.npmjs.com/package/@types/node/v/24.19.2 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| @types/react | 19.3.0 | MIT | https://www.npmjs.com/package/@types/react/v/19.3.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| @types/react-dom | 19.3.0 | MIT | https://www.npmjs.com/package/@types/react-dom/v/19.3.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| @vitejs/plugin-react | 6.1.2 | MIT | https://www.npmjs.com/package/@vitejs/plugin-react/v/6.1.2 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| typescript | 7.0.2 | Apache-2.0 | https://www.npmjs.com/package/typescript/v/7.0.2 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| vite | 8.3.5 | MIT | https://www.npmjs.com/package/vite/v/8.3.5 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| vitest | 5.0.5 | MIT | https://www.npmjs.com/package/vitest/v/5.0.5 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| mapshaper | 0.7.98 | MPL-2.0 | https://www.npmjs.com/package/mapshaper/v/0.7.98 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| http-server | 14.1.1 | MIT | https://www.npmjs.com/package/http-server/v/14.1.1 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |

## Herramientas y fuentes tipográficas

| Componente | Versión | Licencia | Enlace | Cómo se cita | Quién lo agregó | Fecha |
|-|-|-|-|-|-|-|
| tippecanoe (WSL, apt) | v2.49.0 | BSD-2-Clause, leído de /usr/share/doc/tippecanoe/copyright | https://github.com/felt/tippecanoe | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| pmtiles CLI (Protomaps), herramientas/bin, no versionado | 1.31.2 | BSD-3-Clause, según herramientas/bin/LICENSE del prototipo | PENDIENTE | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| IBM Plex Sans | 5.3.0 (@fontsource) | OFL-1.1, src/web/public/fuentes/OFL.txt | https://www.npmjs.com/package/@fontsource/ibm-plex-sans/v/5.3.0 | No requiere cita | Daniel (orquestador de datos) | 2026-11-14 |
| NASA POWER, API diaria de punto, comunidad AG (T-D5; fuentes MERRA-2 y CERES SYN1deg) | PENDIENTE (la API no declara versión) | Política de datos de NASA, CC0 salvo restricción marcada, igual que la fila de POWER de D-012; el CSV no marca restricción | https://power.larc.nasa.gov/docs/ | Texto de reconocimiento de POWER, ver CITAS.md | Claude Code (constructor T-D5) | 2026-11-14 | FUENTE |
| GPM IMERG Final Run daily V07 (GPM_3IMERGDF.07), lectura OPeNDAP de una celda por lote | 07 (archivos V07B) | Guía de uso y cita de EOSDIS, igual que las filas de IMERG anteriores | https://www.earthdata.nasa.gov/engage/open-data-services-software/data-use-policy | Cita de IMERG, DOI de la versión diaria PENDIENTE | Claude Code (constructor T-D5) | 2026-11-14 | FUENTE |
| HLS HLSL30 v2.0 y HLSS30 v2.0, solo capa Fmask (LP DAAC) | 2.0 | "Openly shared, without restriction" según la página del catálogo Earthdata de HLSL30; HLSS30 no leída aparte | https://www.earthdata.nasa.gov/data/catalog/lpcloud-hlsl30-2.0 | Neigh et al. (2021), ver CITAS.md | Claude Code (constructor T-D5) | 2026-11-14 | FUENTE |
| SoilGrids 2.0 por API REST (puntos de lote DEMO, 250 m con cuantiles) | 2.0 | CC BY 4.0 según el Gemelo y el prototipo; sin confirmar en página de ISRIC | PENDIENTE | Poggio et al. 2021, ver CITAS.md | Claude Code (constructor T-D5) | 2026-11-14 | PENDIENTE |
| GHCN-Daily (estaciones USC00255362 y COM00080370), solo mencionadas como referencia en lotes_demo.json; no se descargan datos | no aplica | PENDIENTE, no se inventa | PENDIENTE | No aplica mientras no se use | Claude Code (constructor T-D5) | 2026-11-14 | PENDIENTE |
