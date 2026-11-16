# AGROVERSEx open dataset

Data card for the open dataset released as a GitHub release of the public repository `Daniel-JP10/agroversex-teselas` (decision D-044). The boundary tiles of the app are already published in that repository (decision D-040). Built for the NASA Space Apps Challenge 2026, challenge Field Shift: Adapting Farms with NASA Data.

The plots named `DEMO-USA-01` (Saunders, Nebraska) and `DEMO-COL-01` (Ipiales, Nariño) are illustrative DEMO plots drawn over cropland pixels; they are not identified farms.

Results derived from GHCN-Daily station records are not part of this dataset (see "Excluded files").

## Files

37 files, 2,724,851,806 bytes in total, measured on disk on 2026-11-15. The machine-readable list is `herramientas/dataset_lista.json`; `herramientas/armar_release_dataset.py` builds the flat release folder from it, checks size and SHA-256 of every file and writes `SHA256SUMS.txt` (check a download with `sha256sum -c SHA256SUMS.txt`).

Source path: `consolidados/...` and `pi_d1_mundo.json` are relative to `AGROVERSEX_DATOS/series_mundo` (not versioned in the code repository); the other paths are relative to the code repository root.

| Release name | Source path | Bytes | SHA-256 |
|-|-|-|-|
| `serie_mensual_humedad_radicular_area.csv.gz` | `consolidados/serie_mensual_humedad_radicular_area.csv.gz` | 376,499,761 | `9b129797a15ae40b608637a7f89c81f7d917c21a331f2e3defb70c11f00b26ac` |
| `serie_mensual_humedad_radicular_cultivo.csv.gz` | `consolidados/serie_mensual_humedad_radicular_cultivo.csv.gz` | 361,508,329 | `9a5e52659d5b50c8b95b2cd689c019bc2567413471f1638cb72cc814df87769a` |
| `serie_mensual_ndvi_area.csv.gz` | `consolidados/serie_mensual_ndvi_area.csv.gz` | 380,437,948 | `1d42c0019b14e0a7227ee78c218d4bd2a705646c75bf3ca6bfc3c7dff47ce153` |
| `serie_mensual_ndvi_cultivo.csv.gz` | `consolidados/serie_mensual_ndvi_cultivo.csv.gz` | 347,470,642 | `145c436df585abb815be70fd87b2a899f5d9133f639091f54feff9314039cd49` |
| `serie_mensual_precipitacion_final_area.csv.gz` | `consolidados/serie_mensual_precipitacion_final_area.csv.gz` | 329,197,469 | `96e1f3fa8c3e0a238bf6c4d736d1bb378c75d42b9c419cbd34779c688ce39f8e` |
| `serie_mensual_precipitacion_final_cultivo.csv.gz` | `consolidados/serie_mensual_precipitacion_final_cultivo.csv.gz` | 311,928,834 | `34c667fd1c01177ed790c7cdca5afead43b460b4d495029104a60fa8d98e8c7d` |
| `serie_mensual_precipitacion_late_area.csv.gz` | `consolidados/serie_mensual_precipitacion_late_area.csv.gz` | 15,346,542 | `4bb01625035c12231ca8c6d321ac89cc17478deeef4bd0a650feb873a7b2d49a` |
| `serie_mensual_precipitacion_late_cultivo.csv.gz` | `consolidados/serie_mensual_precipitacion_late_cultivo.csv.gz` | 14,511,003 | `fd82476f3177faf59a8c638e72ad269677816bb88477c5b6031072eb7ffc1e85` |
| `serie_mensual_t2m_area.csv.gz` | `consolidados/serie_mensual_t2m_area.csv.gz` | 293,697,754 | `53ab2ac0428dfa0915f55ba35fb336bbd03cbd7730535f631b2f2db546e17c7a` |
| `serie_mensual_t2m_cultivo.csv.gz` | `consolidados/serie_mensual_t2m_cultivo.csv.gz` | 289,462,715 | `88e8a862483222c98fb5c4eebd2622c3d6711d176c99e27e282fb9ad114df3b3` |
| `pi_d1_mundo.json` | `pi_d1_mundo.json` | 9,666 | `c53ea1af276cca9773c7254cb8de047cc903f39dcb80eeb8ae629d55f64351b8` |
| `gemelo_indice.json` | `src/web/public/gemelo/indice.json` | 16,451 | `c90e300f4975743809716a2373cb7028058d04ae5d6d259dbefb4cf5df923f55` |
| `gemelo_textos_en.json` | `src/web/public/gemelo/textos/en.json` | 15,076 | `793a303bdf204a7f7d2840ae944fe13e640538235e5471ccae774031bc8e8d66` |
| `gemelo_textos_es.json` | `src/web/public/gemelo/textos/es.json` | 16,001 | `2af8f27f800490bc2bb93bb1ae8937b6120d2fbbed97723b761ae36267e1694e` |
| `gemelo_DEMO-COL-01_lote.json` | `src/web/public/gemelo/DEMO-COL-01/lote.json` | 7,420 | `5838da8aeca5c8cd78b3def820b5d248043c9eab8be5fc7e863b653758c2984e` |
| `gemelo_DEMO-USA-01_lote.json` | `src/web/public/gemelo/DEMO-USA-01/lote.json` | 7,401 | `c1a83f2d9ca8f28599d8068c739889199799797fb0b390821483d0dc4411baee` |
| `gemelo_DEMO-USA-01_optimizacion_historico.json` | `src/web/public/gemelo/DEMO-USA-01/optimizacion_historico.json` | 427,894 | `92f3f6d436646db6c1eec994395beb57da4f33bd8502f1038024ba5ee3f508cc` |
| `gemelo_DEMO-USA-01_optimizacion_humedo.json` | `src/web/public/gemelo/DEMO-USA-01/optimizacion_humedo.json` | 333,716 | `3966d3418376c4d5686637a8771dd48d6a93a9e236766d31485d470c0cc67ccb` |
| `gemelo_DEMO-USA-01_optimizacion_normal.json` | `src/web/public/gemelo/DEMO-USA-01/optimizacion_normal.json` | 422,013 | `7432d4b48d9188fc5be175f2431e678e7a9ac5484c6f09d6833974cae6ae4321` |
| `gemelo_DEMO-USA-01_optimizacion_seco.json` | `src/web/public/gemelo/DEMO-USA-01/optimizacion_seco.json` | 423,004 | `2d726341a5caaa96e9a38591a5fcc56f55403ea48309bf19b21f0e90028de6f5` |
| `gemelo_DEMO-USA-01_simulacion_enso_neutra.json` | `src/web/public/gemelo/DEMO-USA-01/simulacion_enso_neutra.json` | 188,788 | `4b949013a3b7fa470bf13692f55f2b44e8d4f3a2ee2dc657c7cf5a3396772070` |
| `gemelo_DEMO-USA-01_simulacion_enso_nina.json` | `src/web/public/gemelo/DEMO-USA-01/simulacion_enso_nina.json` | 188,627 | `e645cdfc6e0b9c1fefe8882f9127f3649bc8cbda99c337d9d8a721c59a530257` |
| `gemelo_DEMO-USA-01_simulacion_enso_nino.json` | `src/web/public/gemelo/DEMO-USA-01/simulacion_enso_nino.json` | 188,080 | `d1a4e5d7a5146a406c80c84b2e8a633df20a049e6920236f6fe6f045a214e58f` |
| `gemelo_DEMO-USA-01_simulacion_historico.json` | `src/web/public/gemelo/DEMO-USA-01/simulacion_historico.json` | 199,386 | `79c097faa71f6c931aaab6cfc2064b06a40ac67590539c8a3c791504b3552638` |
| `gemelo_DEMO-USA-01_simulacion_humedo.json` | `src/web/public/gemelo/DEMO-USA-01/simulacion_humedo.json` | 189,289 | `89919b7d774a9b622f9463a990f2a88375dadda383e9413f453d60176ca94c73` |
| `gemelo_DEMO-USA-01_simulacion_normal.json` | `src/web/public/gemelo/DEMO-USA-01/simulacion_normal.json` | 188,114 | `11d2c71f6304e72665a8dd08f34405c5c0280d02dc8b87fae85820508240512a` |
| `gemelo_DEMO-USA-01_simulacion_seco.json` | `src/web/public/gemelo/DEMO-USA-01/simulacion_seco.json` | 186,105 | `8c8c8f48dd803196da2e68b9faa44bb8cfe8726e97e76127c193cfbd3a7ec94a` |
| `exposicion_erosiva_lotes.json` | `datos/lotes/exposicion_erosiva_lotes.json` | 13,811 | `0a9c682da97e9cbee88180e92a721b1c2dbca7332542d974bdb69918f5e29902` |
| `hls_validez_DEMO-COL-01.json` | `datos/lotes/hls_validez_DEMO-COL-01.json` | 5,047 | `7acd5b2b1054041102504ca7e95a59d4e62b62267ea29a327d79b952e285185f` |
| `hls_validez_DEMO-USA-01.json` | `datos/lotes/hls_validez_DEMO-USA-01.json` | 5,495 | `d4157334a910d8890e3ffbef005a2d4ee34445efc17f4bfe8a654d875436226b` |
| `hls_validez_resumen.md` | `datos/lotes/hls_validez_resumen.md` | 1,685 | `73b4e0a019d6d0331ec977f2a68c2315ef5c6d40a633ba5f099aa6812dece980` |
| `imerg_DEMO-COL-01_diario.csv` | `datos/lotes/imerg_DEMO-COL-01_diario.csv` | 261,786 | `86868ece0a9a5ef4e88ce83ea95d2725182ac9da74d11496b19f5c74b7248309` |
| `imerg_DEMO-USA-01_diario.csv` | `datos/lotes/imerg_DEMO-USA-01_diario.csv` | 258,547 | `5fab55bd6d06223914fc8c63e3f03645223e8a22d1a33a68c8bb1fecf79d10a8` |
| `parametros_suelo_DEMO-COL-01.json` | `datos/lotes/parametros_suelo_DEMO-COL-01.json` | 2,292 | `3f2747ef61d67632918606c315b43526de8b80815a1dda99eda2651aa3e61400` |
| `parametros_suelo_DEMO-USA-01.json` | `datos/lotes/parametros_suelo_DEMO-USA-01.json` | 2,252 | `8c391c7086fc69c3c29b5b2afc9d8c6064998c41d9f3d73b4976445aabda9e78` |
| `power_DEMO-COL-01_diario.csv` | `datos/lotes/power_DEMO-COL-01_diario.csv` | 615,766 | `aadf7a326467759f703e3aabdf3f93cd84522ba3f1c3d92f0c255fd0ad11d222` |
| `power_DEMO-USA-01_diario.csv` | `datos/lotes/power_DEMO-USA-01_diario.csv` | 617,097 | `315a5ae63e2bd4c9c99cfd980180520310c4122db869780ac9deb505b4862fac` |

## Description by file group

### World monthly series per administrative unit (10 files)

`serie_mensual_<variable>_<area|cultivo>.csv.gz`, gzip-compressed CSV with columns `unidad_id, nivel, variable, mes, valor, p10, p90, tipo_rango, frac_valida, ponderacion, producto, version, estado, unidad, motivo`.

- Spatial unit: every geoBoundaries CGAZ unit of levels 0, 1 and 2 (`nivel`), keyed by `unidad_id` (for example `COL-ADM0`). Values are averages of the source grid cells inside each unit.
- Weighting (`ponderacion`): `area` weights cells by their area in the unit; `cultivo` weights them by cropland, using the GFSAD 1 km crop mask (GFSAD1KCM V001).
- Range: `p10` and `p90` are the 10th and 90th percentiles of the cells inside the unit (`tipo_rango` = `espacial`); `frac_valida` is the fraction of the unit with valid data.

| Variable (file) | Unit (column `unidad`) | Source product and version | Source grid | Months (UTC) | `estado` |
|-|-|-|-|-|-|
| `precipitacion_final` | mm/hr (monthly mean rate) | GPM IMERG Final Run monthly, GPM_3IMERGM V07 (files 07B) | 0.1° | 2000-01 to 2025-09, 309 months | final |
| `precipitacion_late` | mm/day (daily values aggregated to month in UTC) | GPM IMERG Late Run daily, GPM_3IMERGDL V07 (files 07B) | 0.1° | 2025-10 to 2026-10, 13 months | provisional |
| `t2m` | K | MERRA-2 M2TMNXSLV (tavgM_2d_slv_Nx), T2M, 5.12.4 | 0.5° x 0.625° | 2000-01 to 2026-09, 321 months | final |
| `humedad_radicular` | kg m-2 | GLDAS Noah monthly, GLDAS_NOAH025_M V2.1, RootMoist_inst (land surface MODEL) | 0.25° | 2000-01 to 2026-07, 319 months | final |
| `ndvi` | 1 (dimensionless) | MODIS Terra MOD13C2 V061, NDVI | 0.05° | 2000-02 to 2026-10, 321 months | final |

Month ranges and counts were read from the `mes` column of each file; the `area` and `cultivo` files of each variable cover the same months.

License: ODbL 1.0 (D-042 point 3), attribution to geoBoundaries (CC BY 4.0) and Runfola et al. (2020). Required citation: the source product (see "Source products") and geoBoundaries.

### `pi_d1_mundo.json`

Summary statistics of the difference between cropland-weighted and area-weighted values (PI-D1 sensitivity), per variable and level: number of months and agricultural units, percentiles of the relative or absolute difference and fraction of unit-month pairs above 2 %, 5 % and 10 %. It holds no per-unit values. License: CC BY 4.0, as a Produced Work of the ODbL series (D-042 point 4), with the ODbL and geoBoundaries notice. Required citation: AGROVERSEx, the source products of the series and geoBoundaries.

### Digital twin packages (16 files, `gemelo_*`)

JSON packages of the digital twin (contract `contratos/gemelo_api.md`): `lote.json` (plot sheet), `simulacion_<scenario>.json` and `optimizacion_<scenario>.json` for the scenarios historico, seco, normal, humedo and ENSO neutral, La Niña and El Niño, plus `indice.json` and the interface texts `textos/en.json` and `textos/es.json`.

- Nature: model simulation, not observation. Daily time step on a nominal 365-day calendar, 3-year horizon, ensembles of strategies, climate and parameter members; outputs reported as p10, p50 and p90.
- Climate forcing: NASA POWER daily, 2001 to 2024 (`power_DEMO-*_diario.csv`). Soil: SoilGrids 2.0 parameters (`parametros_suelo_DEMO-*.json`). ENSO scenarios: NOAA CPC ONI.
- Only `DEMO-USA-01` simulation and optimization packages are included. For `DEMO-COL-01` only `lote.json` is included: its simulation and optimization packages embed the comparison with GHCN-Daily station COM00080370 (see "Excluded files"). `indice.json` still lists the `DEMO-COL-01` packages, which are not in this release.

License: CC BY 4.0 (D-042 point 2). Required citation: AGROVERSEx, NASA POWER and SoilGrids 2.0.

### DEMO plot outputs (10 files)

| File | Content | Units and resolution | Period | Source |
|-|-|-|-|-|
| `power_DEMO-*_diario.csv` | Daily PRECTOTCORR, T2M, T2M_MAX, T2M_MIN, RH2M, ALLSKY_SFC_SW_DWN, WS2M and temperatures corrected to plot elevation (lapse -0.0065 C/m); POWER header kept | mm/day, C, %, MJ/m^2/day, m/s; one point per plot (MERRA-2 cell 0.5° x 0.625°) | 2001-01-01 to 2024-12-31, local solar time | NASA POWER daily API, AG community (MERRA-2 5.12.4 and CERES SYN1deg) |
| `imerg_DEMO-*_diario.csv` | Daily precipitation of the IMERG cell of each plot and number of half-hourly samples | mm/day; one 0.1° cell | 2001-01-01 to 2024-12-31, UTC | GPM IMERG Final Run daily, GPM_3IMERGDF V07 (files 07B) |
| `parametros_suelo_DEMO-*.json` | Sand, clay, organic matter, soil organic carbon, Williams erodibility K and derived parameters, with quantiles | 0 to 1.0 m depth; SoilGrids 250 m point query | static | SoilGrids 2.0 REST API (ISRIC) |
| `hls_validez_DEMO-*.json`, `hls_validez_resumen.md` | Fraction of valid (clear) HLS observations per pixel and month from the Fmask layer | fraction 0 to 1; 30 m pixels of the plot window | 2022-01-01 to 2024-12-31 | HLS HLSL30 and HLSS30 v2.0, Fmask only |
| `exposicion_erosiva_lotes.json` | Erosive rain exposure of each plot: rainfall from NASA POWER as base and IMERG as sensitivity, relief from NASADEM (slope, elevation) and soil erodibility | see the file; NASADEM 1 arc second (~30 m) in a metric UTM CRS | 2001-01-01 to 2024-12-31 | NASA POWER, GPM_3IMERGDF V07, NASADEM_HGT V001, SoilGrids 2.0 |

License: CC BY 4.0 (D-042 point 2); third-party inputs keep their own terms (SoilGrids 2.0 is CC BY 4.0). Required citation: AGROVERSEx and each source product listed in the row.

## Source products

| Product | Version | DOI or reference |
|-|-|-|
| GPM IMERG Final Precipitation L3 1 month 0.1° (GPM_3IMERGM) | V07 (07B) | https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07 |
| GPM IMERG Late Precipitation L3 1 day 0.1° (GPM_3IMERGDL) | V07 (07B) | https://doi.org/10.5067/GPM/IMERGDL/DAY/07 |
| GPM IMERG Final Precipitation L3 1 day 0.1° (GPM_3IMERGDF) | V07 (07B) | https://doi.org/10.5067/GPM/IMERGDF/DAY/07 |
| MERRA-2 tavgM_2d_slv_Nx (M2TMNXSLV) | 5.12.4 | https://doi.org/10.5067/AP1B0BA5PD2K |
| GLDAS Noah Land Surface Model L4 monthly 0.25° (GLDAS_NOAH025_M) | 2.1 | https://doi.org/10.5067/SXAVCZFAQLNO |
| MODIS/Terra Vegetation Indices Monthly L3 Global 0.05Deg CMG (MOD13C2) | 061 | https://doi.org/10.5067/MODIS/MOD13C2.061 |
| GFSAD Crop Mask 2010 Global 1 km (GFSAD1KCM) | 001 | https://doi.org/10.5067/MEaSUREs/GFSAD/GFSAD1KCM.001 |
| NASA POWER daily point API, AG community | API v2 (MERRA-2 5.12.4 and CERES SYN1deg) | https://power.larc.nasa.gov/docs/referencing/ |
| HLS HLSL30 | 2.0 | https://doi.org/10.5067/HLS/HLSL30.002 |
| HLS HLSS30 (NASA product made with ESA/Copernicus Sentinel-2 imagery) | 2.0 | citation pending in `CITAS.md` |
| NASADEM Merged DEM Global 1 arc second (NASADEM_HGT) | 001 | https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001 |
| SoilGrids 2.0 (ISRIC) | 2.0 | https://doi.org/10.5194/soil-7-217-2021 |
| NOAA CPC Oceanic Niño Index (ERSST.v6) | v6 | see `CITAS.md` |
| geoBoundaries CGAZ | commit 4004e96, line 6.0.0 | https://doi.org/10.1371/journal.pone.0231866 |

NASA POWER citation text: "The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division." Full citations of every product: `CITAS.md`; licenses: `LICENCIAS_TERCEROS.md`.

## Excluded files

Excluded because they hold data or aggregates from GHCN-Daily stations (decisions D-038 and D-042; WMO Resolution 40, non-commercial):

| File | Reason | How it could be separated (not done) |
|-|-|-|
| `datos/lotes/validacion_temperatura_ipiales.json` | Validation against GHCN-Daily station COM00080370 | Not separable: the whole file is a GHCN-derived result |
| `datos/lotes/comparacion_power_imerg.json` | Mixes the POWER vs IMERG comparison with the `contraste_estacion_ghcn_*` blocks | Write a copy without the `contraste_estacion_ghcn_*` blocks and with a new SHA-256 |
| `src/web/public/gemelo/DEMO-COL-01/simulacion_*.json` and `optimizacion_*.json` (11 files) | Embed the rainfall and temperature comparison with station COM00080370 | Regenerate the packages without the station comparison block |
| `datos/lotes/lotes_demo.json` | Names the GHCN-Daily reference stations of each plot (`estacion_referencia`); it holds no station values | Drop the `estacion_referencia` field; the app copy is `src/web/public/datos/lotes_demo.json` |

Also left out because they are not data outputs: `datos/lotes/SHA256SUMS.txt` (replaced by the release `SHA256SUMS.txt`) and `datos/lotes/evidencia_red.txt` (test evidence).

## Licenses

See `LICENSE-DATA.md`. In short: series per administrative unit under ODbL 1.0 with attribution to geoBoundaries (CC BY 4.0) and Runfola et al. (2020); the other team data and the documentation under CC BY 4.0; GHCN-Daily derivatives excluded.

The values are estimates with ranges, for decision support. They do not replace the judgment of the farmer or the local advisor.
