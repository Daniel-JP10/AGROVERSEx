# asistido por SI: Claude Code (Anthropic), pruebas de unidades CGAZ sobre datos descargados (T-D1)
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
import pytest
import shapely

from simulacion.config import CRUDOS, PROCESADOS
from simulacion.geo import unidades as u

GPKG = PROCESADOS / "unidades.gpkg"
CONTRATO = Path(__file__).parents[2] / "contratos/unidades.md"

pytestmark = [pytest.mark.datos_reales, pytest.mark.skipif(not GPKG.exists(), reason="falta unidades.gpkg")]


@pytest.fixture(scope="module")
def capas():
    return {n: pyogrio.read_dataframe(GPKG, layer=f"adm{n}") for n in (0, 1, 2)}


@pytest.fixture(scope="module")
def t(capas):
    return pd.concat([c.drop(columns="geometry") for c in capas.values()], ignore_index=True)


def test_conteos_iguales_a_los_de_cgaz(capas):
    for n, c in capas.items():
        ruta = CRUDOS / f"cgaz/geoBoundariesCGAZ_ADM{n}.gpkg"
        if ruta.exists():
            assert len(c) == pyogrio.read_info(ruta)["features"]


def test_sin_duplicados_de_unidad_id(t):
    assert u.duplicados(t) == 0
    assert all(g.unidad_id.is_unique for _, g in t.groupby("nivel"))


def test_todo_padre_existe_en_el_nivel_superior(t):
    por_nivel = {n: set(g.unidad_id) for n, g in t.groupby("nivel")}
    assert t[t.nivel == 0].padre_id.isna().all()
    for n in (1, 2):
        h = t[t.nivel == n]
        assert h.padre_id.notna().all() and h.padre_id.isin(por_nivel[n - 1]).all()
    # el padre es del mismo país
    pais = t.set_index("unidad_id").iso3
    h = t[t.nivel > 0]
    assert (h.padre_id.map(pais).values == h.iso3.values).all()


def test_codigos_de_pais_existen_en_adm0(t):
    assert u.codigos_huerfanos(t) == set()
    assert (t[t.iso3 == "XKX"].nivel == 0).sum() == 1 and not t.iso3.isin(["XKO"]).any()


def test_geometrias_validas_y_poligonales(capas):
    for c in capas.values():
        assert shapely.is_valid(c.geometry.values).all()
        assert set(c.geometry.geom_type) <= {"Polygon", "MultiPolygon"}


def test_area_proyectada_sobre_geodesica_dentro_de_tolerancia(capas):
    for n, c in capas.items():
        r = c.area_km2.values / u.area_geodesica_km2(c.geometry.values)
        assert (c.area_km2 > 0).all()
        assert np.abs(r - 1).max() < u.TOLERANCIA_AREA, (n, np.abs(r - 1).max())


def test_colombia_y_ipiales(t):
    col = t[t.iso3 == "COL"]
    assert (col.nivel == 1).sum() == 33 and (col.nivel == 2).sum() == 1122
    ip = col[col.nombre == "Ipiales"].iloc[0]
    assert col.set_index("unidad_id").nombre[ip.padre_id] == "Nariño"


def test_colombia_contra_divipola(t):
    csv = CRUDOS / "divipola/divipola_gdxc-w37w.csv"
    if not csv.exists():
        pytest.skip("falta la DIVIPOLA descargada")
    from simulacion.geo.colombia import comparar_divipola
    col = t[(t.iso3 == "COL") & (t.nivel == 2)]
    dep = t.set_index("unidad_id").nombre
    r = comparar_divipola(col.assign(dpto=col.padre_id.map(dep)), pd.read_csv(csv, dtype=str))
    assert r["cgaz"] == r["dane"] == 1122
    # mismo número de municipios; las diferencias son de nombre y quedan listadas en el informe (menos del 1 %)
    assert len(r["sobran_en_cgaz"]) == len(r["faltan_en_cgaz"]) < 0.01 * r["dane"]
    assert r["exactos"] + len(r["variantes"]) + len(r["sobran_en_cgaz"]) == 1122


def test_lista_sin_nivel2_sale_de_los_datos_y_esta_en_el_contrato(t):
    sin = u.paises_sin_nivel2(t[t.nivel == 2])
    assert "COL" not in sin and "AND" in sin and "LBY" in sin
    texto = CONTRATO.read_text(encoding="utf-8")
    assert all(p in texto for p in sin)
    assert f"Son {len(sin)} unidades de país o zona" in texto
