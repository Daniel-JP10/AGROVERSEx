# Data and documentation licenses

This file applies decision D-042 of `decisiones/registro.md`. The source code is under the Apache License 2.0 (`LICENSE`). Third-party data and software keep their own licenses, listed in `LICENCIAS_TERCEROS.md`.

## CC BY 4.0

License: Creative Commons Attribution 4.0 International, https://creativecommons.org/licenses/by/4.0/

Applies to data produced by the team that do not depend on administrative boundaries, and to the team's documentation:

- digital twin packages (`src/web/public/gemelo/`), except the files listed under "Excluded";
- sheets and outputs of the DEMO plots (`datos/lotes/`), except the files listed under "Excluded";
- the NASADEM block and profile images of the DEMO plots (`src/web/public/lotes/`) and the team's own figures;
- documentation (`README.md`, `DATASET.md`, `contratos/`, `decisiones/` and the other team documents).

Maps, images and charts made from the series organized by administrative unit are Produced Works under ODbL 1.0 §4.5: they are released under CC BY 4.0 and carry the ODbL and geoBoundaries notice next to each one.

## ODbL 1.0

License: Open Data Commons Open Database License 1.0, https://opendatacommons.org/licenses/odbl/1-0/

Applies to the administrative boundary layers and to every dataset organized by administrative unit:

- boundary tiles (`adm0`, `adm1`, `adm2` `.pmtiles`), `unidades.gpkg` and the search index;
- the monthly series per unit: `src/web/public/datos/COL/*.json.gz` and the world series `serie_mensual_<variable>_<area|cultivo>.csv.gz`, with their manifest.

Attribution required: geoBoundaries CGAZ, released under CC BY 4.0, and Runfola, D. et al. (2020). geoBoundaries: A global database of political administrative boundaries. PLoS ONE 15(4): e0231866. https://doi.org/10.1371/journal.pone.0231866

## Excluded from the open licenses

Results derived from GHCN-Daily station records (NOAA NCEI) are not covered by CC BY 4.0 or ODbL 1.0 and are not part of the open dataset (decisions D-038 and D-042). Data from stations outside the United States are exchanged under WMO Resolution 40 and may only be used for research, education and other non-commercial purposes. In this repository that covers:

- `datos/lotes/validacion_temperatura_ipiales.json`;
- the `contraste_estacion_ghcn_*` block of `datos/lotes/comparacion_power_imerg.json`;
- the GHCN station comparison embedded in the digital twin packages of `DEMO-COL-01` (`simulacion_*.json`, `optimizacion_*.json`);
- any other file holding GHCN station data or aggregates.

The license statements above are the team's reading of each license (INFERENCE, not legal advice).
