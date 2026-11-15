# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Lotes sintéticos (F13, INICIAR §8.6) y sus series diarias.

Los lotes son rectángulos sintéticos dentro de unidades ADM1, sin persona ni finca real asociada.
Todo parámetro sin ficha es SUPUESTO con revisión 2026-11-13; lo que depende de una ficha ausente es PENDIENTE.
"""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from shapely.geometry import box
from shapely.prepared import prep

from simulacion import config
from simulacion.azar import rng_unidad
from simulacion.cobertura import cobertura_simulada
from simulacion.tiempo import dia_id

N_DIAS = dia_id(config.FECHA_FIN_DIARIA) + 1
N = config.N_MESES
ZONAS_YAML = Path(__file__).resolve().parent / "zonas_agroversex.yaml"
# En un worktree los datos viven en el repositorio principal: se sube hasta el primer padre que los tiene
_RAIZ_DATOS = next((q for q in Path(__file__).resolve().parents if (q / "datos/procesados").exists()), config.RAIZ)
GPKG_UNIDADES = _RAIZ_DATOS / "datos/procesados/unidades.gpkg"
GPKG_GADM = _RAIZ_DATOS / "datos/crudos/gadm_extraido/gadm_410-levels.gpkg"

# Pico de NDVI por cultivo. Maíz y soya: FUENTE INV-VEG §8 (INICIAR §13.2). Resto: SUPUESTO, PENDIENTE de ficha
PICO_NDVI = {"maiz": (0.78, 0.86), "soya": (0.87, 0.91)}
PICO_SUPUESTO = (0.70, 0.85)
NDVI_SUELO = 0.20          # SUPUESTO: NDVI de suelo expuesto
UMBRAL_NDVI = 0.35         # SUPUESTO: bajo este valor el suelo cuenta como expuesto
UMBRAL_NBR2 = 0.15         # SUPUESTO: sobre este valor, suelo expuesto (solo desde abril de 2013)
LADO_KM = (0.5, 1.5)       # SUPUESTO: lado del rectángulo sintético

# Cadencia de revisita por sensor: PENDIENTE de ficha EV-VEG; los días son SUPUESTO
REVISITA_DIAS = {"l5": 16, "l7": 16, "l30": 16, "s30": 5}
PROB_SLC_OFF = 0.78        # SUPUESTO: fracción de pasadas de Landsat 7 utilizables tras 2003-05-31
F_L5_FIN, F_L7_SLC, F_L7_FIN = date(2012, 5, 5), date(2003, 5, 31), date(2013, 3, 31)
F_L30, F_S30 = date(2013, 4, 1), date(2015, 11, 1)
NUBE_BASE, NUBE_LLUVIA = 0.20, 0.50   # SUPUESTO: prob. diaria de nube = base + k * lluvia/(lluvia+100)
SESGO_SENSOR, RUIDO_SENSOR = 0.02, 0.03   # SUPUESTO: sesgo y ruido (m3/m3) del sensor propio de humedad
CULTIVOS_FRAC = (11, 13)   # índices IGBP 12 y 14 (cultivo y mosaico)
ETIQ_EROSION = "relieve de unidad, no pendiente del lote"
ETIQ_ESTRES = "contexto de 9 km, no del lote"
ETIQ_HELADA = "contexto de ~0,5°, no del lote"


def cargar_zonas() -> dict:
    return yaml.safe_load(ZONAS_YAML.read_text(encoding="utf-8"))


def geometrias_unidades(ids) -> dict:
    """Geometría de cada unidad: unidades.gpkg con `where` por id; si falta o está bloqueado, el GPKG de GADM."""
    import pyogrio
    ids = sorted(set(ids))
    lista = ",".join(f"'{i}'" for i in ids)
    try:
        out = {}
        for capa in ("adm0", "adm1", "adm2"):
            df = pyogrio.read_dataframe(GPKG_UNIDADES, layer=capa, where=f"id IN ({lista})", columns=["id"])
            out.update(dict(zip(df.id, df.geometry)))
        if set(ids) <= set(out):
            return out
    except Exception:  # archivo ausente o en escritura por la reconstrucción de la fase 1
        pass
    out = {}
    for nivel, col in ((1, "GID_1"), (2, "GID_2")):
        df = pyogrio.read_dataframe(GPKG_GADM, layer=f"ADM_{nivel}", where=f"{col} IN ({lista})", columns=[col])
        out.update(dict(zip(df[col], df.geometry)))
    return out


def _rect(rng, geom, prep_g):
    lon0, lat0, lon1, lat1 = geom.bounds
    for _ in range(200):
        lado = rng.uniform(*LADO_KM)
        x, y = rng.uniform(lon0, lon1), rng.uniform(lat0, lat1)
        dlat = lado / 111.0
        dlon = lado / (111.0 * max(np.cos(np.radians(y)), 0.05))
        r = box(x, y, x + dlon, y + dlat)
        if prep_g.contains(r):
            return r
    return None


def generar_lotes(zona: str, n: int = 50, *, geo: pd.DataFrame | None = None,
                  geometrias: dict | None = None, zonas: dict | None = None) -> list[dict]:
    z = (zonas or cargar_zonas())[zona]
    if geo is None:
        from simulacion.clima import cargar_geo
        geo = cargar_geo()
    ids = [u for u in z["unidades"] if u in geo.index]
    geometrias = geometrias or geometrias_unidades(ids)
    # Peso por fracción de cultivo simulada; sin ninguna, reparto uniforme
    g = geo.loc[ids]
    cob = cobertura_simulada(g, g.get("koppen", -1))
    w = cob[[f"igbp_{i + 1}" for i in CULTIVOS_FRAC]].sum(1).to_numpy() + 1e-3
    rng = rng_unidad(zona, "lotes")
    asigna = rng.choice(len(ids), size=n, p=w / w.sum())
    out = []
    for k, ui in enumerate(asigna):
        u = ids[ui]
        geom = geometrias[u]
        r = _rect(rng, geom, prep(geom))
        if r is None:  # unidad demasiado delgada: sin lote, no se inventa uno fuera
            continue
        cult = z["cultivos"][int(rng.integers(len(z["cultivos"])))]
        lo, hi = PICO_NDVI.get(cult, PICO_SUPUESTO)
        out.append({"id": f"L{zona}-{len(out) + 1}", "unidad_id": u, "geom_wkt": r.wkt, "cultivo_actual": cult,
                    "zona_demo": zona, "pico_ndvi": float(rng.uniform(lo, hi))})
    return out


def mensual_de_unidades(ids, geo) -> dict:
    """Series mensuales de cada unidad con los módulos del generador: {id: dict para serie_diaria}."""
    from simulacion import clima, vegetacion, agua
    g = geo.loc[list(ids)]
    c = clima.generar_clima(list(g.index), slice(None), geo=g)
    nd = vegetacion.generar_ndvi(c, slice(None), g)
    a = agua.generar_agua(c, nd, slice(None), geo=g)
    return {u: {"ndvi": nd["ndvi"][i], "sm_raiz": a.sm_raiz[i], "precip": c.precip[i],
                "dias_helada": c.dias_helada[i], "elev_media": float(g.elev_media.iloc[i])}
            for i, u in enumerate(g.index)}


# --- series diarias ---

_DIAS = np.arange(N_DIAS)
_ANIO = np.array([date.fromordinal(config.FECHA_INICIO.toordinal() + int(d)).year for d in range(N_DIAS)])
_MES = np.array([(date.fromordinal(config.FECHA_INICIO.toordinal() + int(d)).year - 2000) * 12
                 + date.fromordinal(config.FECHA_INICIO.toordinal() + int(d)).month - 1 for d in range(N_DIAS)])
_MES0 = np.searchsorted(_MES, np.arange(N))                      # primer día de cada mes
_MED = _MES0 + np.diff(np.append(_MES0, N_DIAS)) / 2             # centro de cada mes, en días


def _a_diario(x):
    x = np.asarray(x, float)
    ok = np.isfinite(x)
    return np.interp(_DIAS, _MED[ok], x[ok])


def mascaras_pasada(rng) -> dict:
    """Días con pasada de cada sensor. l7_valido descuenta la pérdida por SLC-off desde 2003-05-31."""
    def tren(ini, fin, rev):
        m = np.zeros(N_DIAS, bool)
        d0, d1 = dia_id(ini), dia_id(fin)
        m[d0 + int(rng.integers(rev)):d1 + 1:rev] = True
        return m
    f0, fin_t = config.FECHA_INICIO, config.FECHA_FIN_DIARIA
    r = REVISITA_DIAS
    l5, l7 = tren(f0, F_L5_FIN, r["l5"]), tren(f0, F_L7_FIN, r["l7"])
    l30, s30 = tren(F_L30, fin_t, r["l30"]), tren(F_S30, fin_t, r["s30"])
    l7v = l7 & ~((_DIAS >= dia_id(F_L7_SLC)) & (rng.random(N_DIAS) > PROB_SLC_OFF))
    return {"l5": l5, "l7": l7, "l7_valido": l7v, "l30": l30, "s30": s30, "paso": l5 | l7v | l30 | s30}


def serie_diaria(lote: dict, mensual_unidad: dict, escala_nube: float = 1.0) -> dict:
    """ndvi, nbr2, sm_verdad, sm_sensor, nube de N_DIAS; NaN sin pasada o con nube. Extra: ndvi_verdad."""
    rng = rng_unidad(lote["id"], "serie")
    mu = mensual_unidad
    nd_m = np.asarray(mu["ndvi"], float)
    nd_m = np.where(np.isfinite(nd_m), nd_m, np.nanmin(nd_m))
    u = _a_diario(nd_m)
    f = (u - u.min()) / max(np.ptp(u), 1e-6)
    f = np.clip(f + 0.03 * rng.standard_normal(N_DIAS), 0, 1)
    f[np.argmax(u)] = 1.0  # el pico del ciclo siempre llega al pico del cultivo
    ndvi_v = NDVI_SUELO + (lote["pico_ndvi"] - NDVI_SUELO) * f
    nbr2_v = 0.05 + 0.20 * (1 - f) + 0.02 * rng.standard_normal(N_DIAS)  # SUPUESTO: sin ficha de NBR2

    p = _a_diario(np.asarray(mu["precip"], float))
    # SUPUESTO: nube = base + término saturante en la lluvia mensual (mm/mes; rev. 2026-11-13)
    pn = np.clip((NUBE_BASE + NUBE_LLUVIA * p / (p + 100.0)) * escala_nube, 0, 0.95)
    nube = (rng.random(N_DIAS) < pn).astype(np.int8)

    ok = mascaras_pasada(rng)["paso"] & (nube == 0)
    ndvi = np.where(ok, ndvi_v, np.nan)
    nbr2 = np.where(ok & (_DIAS >= dia_id(F_L30)), nbr2_v, np.nan)

    sm = _a_diario(mu["sm_raiz"]) * (1 + 0.05 * rng.standard_normal())
    sm_v = np.clip(sm + 0.005 * rng.standard_normal(N_DIAS), 0, None)
    sm_s = np.clip(sm_v + SESGO_SENSOR + RUIDO_SENSOR * rng.standard_normal(N_DIAS), 0, None)
    return {"ndvi": ndvi, "nbr2": nbr2, "sm_verdad": sm_v, "sm_sensor": sm_s, "nube": nube, "ndvi_verdad": ndvi_v}


def _racha(dias, marca):
    """Racha más larga de elementos consecutivos con marca; devuelve (primer día, último día) o None."""
    mejor, ini = None, None
    for i, m in enumerate(marca):
        if m and ini is None:
            ini = i
        if (not m or i == len(marca) - 1) and ini is not None:
            fin = i if m else i - 1
            if mejor is None or dias[fin] - dias[ini] > mejor[1] - mejor[0]:
                mejor = (int(dias[ini]), int(dias[fin]))
            ini = None
    return mejor


def detectar_ventana(ndvi, nbr2, dia, ndvi_verdad=None) -> list[dict]:
    """Ventana de suelo expuesto por año (día-id de inicio y fin). Antes de abril de 2013 solo NDVI.

    Con ndvi_verdad (diaria) calcula error_semanas = media de |desfase inicio| y |desfase fin|, en semanas.
    """
    ndvi, nbr2, dia = (np.asarray(x, float) if k < 2 else np.asarray(x) for k, x in enumerate((ndvi, nbr2, dia)))
    anio = _ANIO[dia]
    out = []
    for a in np.unique(anio):
        s = (anio == a) & np.isfinite(ndvi)
        d, nd, nb = dia[s], ndvi[s], nbr2[s]
        marca = (nd < UMBRAL_NDVI) & (~np.isfinite(nb) | (nb > UMBRAL_NBR2))
        r = _racha(d, marca)
        w = {"anio": int(a), "inicio": None, "fin": None, "detectada": r is not None, "confianza": None,
             "error_semanas": None, "fuente": "ndvi"}
        if r:
            w["inicio"], w["fin"] = r
            dentro = (d >= r[0]) & (d <= r[1])
            if np.isfinite(nb[dentro]).any():
                w["fuente"] = "ndvi+nbr2"
            # SUPUESTO: confianza = pasadas válidas / pasadas esperadas a 16 días en la ventana
            w["confianza"] = float(min(1.0, dentro.sum() / max((r[1] - r[0]) / 16 + 1, 1)))
        if ndvi_verdad is not None:
            sv = anio == a
            rv = _racha(dia[sv], np.asarray(ndvi_verdad)[dia[sv]] < UMBRAL_NDVI)
            if r and rv:
                w["error_semanas"] = float((abs(r[0] - rv[0]) + abs(r[1] - rv[1])) / 2 / 7)
        out.append(w)
    return out


def riesgos_lote(lote: dict, mensual_unidad: dict | None = None) -> dict:
    """Riesgos con su escala honesta. Erosión: PENDIENTE (sin pendiente de 30 m, DEP-F1-4), valor NULL."""
    mu = mensual_unidad or {}
    r = {"erosion": {"valor": None, "relieve_unidad_m": mu.get("elev_media"), "etiqueta": ETIQ_EROSION,
                     "estado": "PENDIENTE: sin pendiente de NASADEM a 30 m"}}
    est = hel = None
    if "sm_raiz" in mu:
        sm = np.asarray(mu["sm_raiz"], float)
        # SUPUESTO: estrés = fracción de meses bajo la mitad (FRAC_ESTRES de agua.py) del percentil 95 de la humedad
        est = float(np.nanmean(sm < 0.5 * np.nanpercentile(sm, 95)))
    if "dias_helada" in mu:
        hel = float(np.nansum(mu["dias_helada"]) / (len(mu["dias_helada"]) / 12))
    r["estres_hidrico"] = {"valor": est, "unidad": "fracción de meses", "etiqueta": ETIQ_ESTRES}
    r["helada"] = {"valor": hel, "unidad": "días/año", "etiqueta": ETIQ_HELADA}
    return r
