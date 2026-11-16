# AGROVERSEx

AGROVERSEx is a decision-support web app built for the NASA Space Apps Challenge 2026, challenge **Field Shift: Adapting Farms with NASA Data**. A farmer or an advisor finds their area on a 3D globe, sees how rainfall, air temperature, root-zone soil moisture and vegetation (NDVI) changed month by month using NASA Earth observations, and compares crop-rotation strategies with a digital twin that shows ranges, not promises.

AGROVERSEx is a decision-support tool; it does not replace the judgment of the farmer or the local advisor.

The two demo fields, `DEMO-USA-01` (Saunders, Nebraska) and `DEMO-COL-01` (Ipiales, Nariño), are illustrative plots drawn over cropland pixels. They are not identified farms.

## Using the app

The menu has six sections:

- **Earth**: the globe with monthly values per country and per first and second administrative level, with the product and version behind each map.
- **Your field**: the digital twin of a demo field, with its climate, soil and relief.
- **Rotations**: rotation strategies compared under historical, dry, normal and wet scenarios and the three ENSO phases, with p10 to p90 ranges.
- **Science and validation**: how the data and the model were checked, including comparisons between products and with ground stations (station results appear only as aggregates).
- **Open data**: every file behind the maps with its size, SHA-256 checksum and license, ready to download.
- **Sources**: data sources, glossary and credits.

Two reading modes, switched in the header:

- **Farmer** keeps to what you need to decide.
- **Technical** adds detail for advisors and analysts: on Earth, the choice between averaging over cropland or over total area, the PI-D1 sensitivity line and the limitations; in Rotations, the trade-offs between strategies, which come without a range; in the glossary, the technical definitions. The data are the same in both modes.

The interface is in English by default, with Spanish available.

## Repository

- `src/web/`: web app (Vite, React, MapLibre).
- `src/mapa_estatico/`: static data files and the deployment step.
- `src/gemelo/`: digital twin (simulation and NSGA-II rotation search).
- `src/lotes_demo/`: data pipeline of the demo fields.
- `pruebas/`: Python tests. `contratos/`: data contracts. `herramientas/`: helper scripts.
- `LICENCIAS_TERCEROS.md`, `CITAS.md`, `SI_USO.md`: third-party licenses, citations and AI-use register (canonical versions in Spanish).

## Reproducing

### Python environments

Python 3.12 and [uv](https://github.com/astral-sh/uv). The lock files are committed with hashes.

```bash
# Windows: data pipeline and tests
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe --require-hashes -r requirements-geo.lock.txt

# WSL Ubuntu 24.04: raster processing (rasterio, exactextract)
uv venv ~/venvs/agroversex_geo --python 3.12
uv pip install --python ~/venvs/agroversex_geo/bin/python --require-hashes -r requirements-geo-wsl.lock.txt

# Digital twin
uv pip install --python .venv/Scripts/python.exe --require-hashes -r requirements-gemelo.lock.txt
```

NASA Earthdata credentials live in `~/.netrc` (set up with `earthaccess.login(persist=True)`), never in the repository.

### Web app build and deployment

```bash
cd src/web
npm ci
VITE_TESELAS_URL=https://daniel-jp10.github.io/agroversex-teselas/ npx vite build
cd ../..
AGROVERSEX_DATOS=<folder with teselas/, indice_busqueda.json.gz, unidades.gpkg and series_mundo/consolidados/> \
AGROVERSEX_TESELAS=<folder with the clean adm0, adm1 and adm2 .pmtiles> \
PYTHONPATH=src python -m mapa_estatico.construir --desplegar src/web/dist
```

The last step copies the boundary tiles and the search index into `dist/teselas/`, builds `dist/datos/unidades_geo.json.gz` and the world series in `dist/datos/`, and fails if a local path is left anywhere in `dist`. `AGROVERSEX_DATOS` is required; `AGROVERSEX_TESELAS` points to the tile copies without internal paths. Details: `contratos/web_datos.md`, sections 6 and 7.

In the public deployment the `.pmtiles` boundary tiles are read from GitHub Pages ([agroversex-teselas](https://github.com/Daniel-JP10/agroversex-teselas)) through `VITE_TESELAS_URL`, because two of them exceed the 25 MiB per-file limit of Cloudflare Pages; without that variable the app reads them from `dist/teselas/`. The search index is always served by the app itself.

Some data scripts assume the local root `C:/NASA/`; adjust it with their environment variable (`AGROVERSEX_DATOS`, `AGROVERSEX_TESELAS`) or by editing the path.

### Tests

```bash
.venv/Scripts/python -m pytest -m "not datos_reales" -q
```

Web unit tests: `cd src/web && npx vitest run`.

### Open dataset

`DATASET.md` describes the open dataset (files, sizes, SHA-256, units, periods, licenses and citations), published as a release of the public repository [Daniel-JP10/agroversex-teselas](https://github.com/Daniel-JP10/agroversex-teselas). `herramientas/armar_release_dataset.py` builds and checks the release folder.

## Data sources

Full list with versions, licenses and citations: `LICENCIAS_TERCEROS.md` and `CITAS.md`.

**NASA**

- GPM IMERG V07: Final monthly (GPM_3IMERGM), Late daily (GPM_3IMERGDL) and Final daily (GPM_3IMERGDF).
- MERRA-2 5.12.4: M2TMNXSLV and M2TMNXRAD.
- GLDAS Noah 2.1 monthly (GLDAS_NOAH025_M).
- SMAP: SPL3SMP_E V006 and SPL4SMGP V008.
- MODIS Terra MOD13C2 V061.
- GFSAD Crop Mask 2010 Global 1 km V001 (GFSAD1KCM), for cropland weighting.
- HLS v2.0, HLSL30 and HLSS30, Fmask layer only.
- NASADEM_HGT V001.
- NASA POWER (daily point API, AG community, and monthly regional API).
- NASA GIBS (MODIS_Terra_CorrectedReflectance_TrueColor and BlueMarble_ShadedRelief_Bathymetry), globe background.

**Partner agencies**

No product is taken directly from ESA or another partner agency. HLSS30 is a NASA product made with Sentinel-2 imagery from ESA/Copernicus.

**Other sources**

- geoBoundaries CGAZ, administrative boundaries (CC BY 4.0; Runfola et al., 2020).
- Natural Earth 1:10m (public domain).
- SoilGrids 2.0, ISRIC (CC BY 4.0), soil of the demo fields.
- NOAA CPC ONI and RONI (ERSST.v6), ENSO context.
- DANE DIVIPOLA, used only to compare municipality codes; not redistributed.
- GHCN-Daily, NOAA NCEI: station records used only for validation. Only aggregates are shown, for non-commercial use (WMO Resolution 40), and they are excluded from the open licenses and from the open dataset.

## Use of AI

AI tools helped write code and documents; the team decided the idea and the approach. Every AI-assisted code file carries an `asistido por SI` header and a row in `SI_USO.md` (tool, file, purpose, date). `SI_USO.md` has 550 rows:

- Claude Code (Anthropic): 489 rows.
- Cursor (agent): 51 rows.
- Antigravity (Google DeepMind): 8 rows.
- Shared rows: 1 Claude Code with Cursor and 1 Claude Code with Antigravity.

## Team

- Daniel Andres Jimenez Povea, director.
- Jostin Andres Colon Ramos, design.
- Emmanuel Ascendra Perez, digital twin.

## License

The AGROVERSEx source code is released under the Apache License 2.0 (`LICENSE`). Data produced by the team that do not depend on administrative boundaries, and the team's documentation, are released under CC BY 4.0. The administrative boundary layers and every dataset organized by administrative unit, including the monthly series per unit, derive from geoBoundaries CGAZ and are released under the Open Database License 1.0, with attribution to geoBoundaries under CC BY 4.0 and to Runfola et al. (2020), https://doi.org/10.1371/journal.pone.0231866. Results derived from GHCN-Daily station records are excluded from these open licenses and may only be used for research, education and other non-commercial purposes. Third-party data and software keep their own licenses, listed in `LICENCIAS_TERCEROS.md`. Details: `LICENSE-DATA.md`.

- Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
- ODbL 1.0: https://opendatacommons.org/licenses/odbl/1-0/
