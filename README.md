# AGROVERSEx

Decision-support tool for the NASA Space Apps Challenge 2026, challenge **Field Shift: Adapting Farms with NASA Data**. A 3D globe where farmers find their area, see how rainfall, temperature, soil moisture and vegetation changed using NASA Earth observations, and compare at least three crop-rotation strategies with ranges, not promises. It supports, and does not replace, farmer judgment and local agricultural expertise.

Status: hackathon work in progress (14–15 November 2026). Values marked SIMULATED are placeholders being replaced with real NASA data.

## Repository

- `src/simulacion/`: data pipeline (being migrated from simulated data and GADM/WorldClim to NASA products and geoBoundaries CGAZ).
- `src/web/`: web app (Vite, React, MapLibre).
- `pruebas/`: Python tests.
- `contratos/`: data contracts between team areas.
- `LICENCIAS_TERCEROS.md`, `CITAS.md`, `SI_USO.md`: third-party licenses, citations and AI-use declaration.

## Environments

Python 3.12 and [uv](https://github.com/astral-sh/uv). Lock files are hashed and committed.

```bash
# Windows: everything except raster processing
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe --require-hashes -r requirements-geo.lock.txt

# WSL Ubuntu 24.04: rasterio and exactextract
uv venv ~/venvs/agroversex_geo --python 3.12
uv pip install --python ~/venvs/agroversex_geo/bin/python --require-hashes -r requirements-geo-wsl.lock.txt

# Regenerate locks after changing a requirements file
uv pip compile requirements-geo.txt --python-version 3.12 --generate-hashes -o requirements-geo.lock.txt
uv pip compile requirements-geo-wsl.txt --python-version 3.12 --python-platform x86_64-unknown-linux-gnu --generate-hashes -o requirements-geo-wsl.lock.txt

# Web app and tools
cd src/web && npm ci && npm run build
cd herramientas && npm ci
```

NASA Earthdata credentials live in `~/.netrc` (set up with `earthaccess.login(persist=True)`), never in the repository.

## Tests

```bash
.venv/Scripts/python -m pytest -m "not datos_reales" -q   # Python, no downloaded data needed
```

Web unit tests (vitest) must be run from **PowerShell**. Under Git Bash every suite fails with "Vitest failed to find the runner"; it is the shell, not the code.

```powershell
cd src\web
npx vitest run
```

## License

Apache License 2.0. See `LICENSE`.
