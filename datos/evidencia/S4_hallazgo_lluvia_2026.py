# asistido por SI: Claude Code (Anthropic), contraste de lluvia 2026-01 y 2026-02 en anomalías
# Reproduce: PYTHONPATH=src C:\NASA\AGROVERSEx\.venv\Scripts\python.exe datos/evidencia/S4_hallazgo_lluvia_2026.py
# Salida: datos/evidencia/S4_hallazgo_lluvia_2026.json (solo agregados; sin series diarias de GHCN)
import csv, gzip, json, os, statistics as st, urllib.request, warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import numpy as np

warnings.filterwarnings("ignore")

DATOS = os.environ.get("AGROVERSEX_DATOS", r"C:\NASA\AGROVERSEx\datos")
SERIES = os.path.join(DATOS, "procesados", "series", "COL")
CACHE = os.path.join(DATOS, "crudos", "power_hallazgo")
GHCN = r"C:\NASA\compartir\ghcn"
SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "S4_hallazgo_lluvia_2026.json")
MESES_HALLAZGO = ["2026-01", "2026-02"]


def leer_serie(nombre, nivel):
    # devuelve {unidad_id: {mes: valor}} solo con el nivel pedido
    out = {}
    with gzip.open(os.path.join(SERIES, nombre), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["nivel"]) == nivel and r["valor"] != "":
                out.setdefault(r["unidad_id"], {})[r["mes"]] = float(r["valor"])
    return out


def imerg(nivel):
    fin = leer_serie("serie_mensual_precipitacion_final_area.csv.gz", nivel)
    late = leer_serie("serie_mensual_precipitacion_late_area.csv.gz", nivel)
    # Final viene en mm/hr y Late en mm/day: todo a mm/day (x24)
    fin = {u: {m: x * 24.0 for m, x in s.items()} for u, s in fin.items()}
    return fin, late


def anomalias_unidad(fin, late):
    # razon Late / climatologia Final del mismo mes calendario (2000 a 2025) y z con la sd de Final
    filas = {}
    for mes, x in late.items():
        v = [fin[f"{a}-{mes[5:]}"] for a in range(2000, 2026) if f"{a}-{mes[5:]}" in fin]
        mu, sd = st.mean(v), st.stdev(v)
        filas[mes] = {"late_mm_dia": x, "clim_mm_dia": mu, "razon": x / mu, "z_vs_final": (x - mu) / sd,
                      "n_clim": len(v), "final_min": min(v), "final_max": max(v)}
    return filas


def puntos_rejilla():
    import geopandas as gpd
    from shapely.geometry import Point
    g = gpd.read_file(os.path.join(DATOS, "procesados", "unidades.gpkg"), layer="adm0")
    col = g[g.unidad_id == "COL-ADM0"].geometry.iloc[0]
    return [(la + 0.5, lo + 0.5) for la in range(-5, 14) for lo in range(-80, -66) if col.contains(Point(lo + 0.5, la + 0.5))]


def power_punto(lat, lon):
    os.makedirs(CACHE, exist_ok=True)
    ruta = os.path.join(CACHE, f"power_{lat}_{lon}.json")
    if not os.path.exists(ruta):
        url = ("https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=PRECTOTCORR&community=AG"
               f"&longitude={lon}&latitude={lat}&start=2000&end=2026&format=JSON")
        for intento in range(3):
            try:
                with urllib.request.urlopen(url, timeout=90) as r:
                    datos = r.read()
                break
            except Exception:
                if intento == 2:
                    raise
        with open(ruta, "wb") as f:
            f.write(datos)
    with open(ruta, encoding="utf-8") as f:
        p = json.load(f)["properties"]["parameter"]["PRECTOTCORR"]
    # el mes 13 es el anual y -999 es relleno: ambos se descartan
    return {f"{k[:4]}-{k[4:]}": v for k, v in p.items() if k[4:] != "13" and v > -990}


def power_colombia():
    pts = puntos_rejilla()
    with ThreadPoolExecutor(4) as ex:
        series = list(ex.map(lambda p: power_punto(*p), pts))
    meses = sorted(set().union(*[s.keys() for s in series]))
    # media simple de puntos de 1 grado (SUPUESTO: sin ponderar por area)
    media = {m: st.mean([s[m] for s in series if m in s]) for m in meses if sum(m in s for s in series) >= 0.9 * len(series)}
    return len(pts), media, series


def indice_cpc(url, col):
    out = {}
    with urllib.request.urlopen(url, timeout=60) as r:
        for ln in r.read().decode().splitlines()[1:]:
            p = ln.split()
            out[f"{p[0]} {p[1]}"] = float(p[col])
    return out


def ghcn_ultima_fecha():
    # solo agregados: ultima fecha con PRCP por estacion; los CSV viven fuera del repo (Resolucion 40 OMM)
    import pandas as pd
    out = {}
    for f in sorted(os.listdir(GHCN)):
        if f.startswith("C") and f.endswith(".csv"):
            d = pd.read_csv(os.path.join(GHCN, f), usecols=["DATE", "PRCP"], dtype={"DATE": str}).dropna()
            out[f[:-4]] = d.DATE.max()
    return out


def ghcn_vs_imerg_final(ultimas):
    # correlacion de anomalias mensuales (razon a la climatologia propia 2000-2024) de la estacion frente a la unidad ADM2 que la contiene
    import pandas as pd, geopandas as gpd
    from shapely.geometry import Point
    pos = {}
    for ln in open(os.path.join(GHCN, "ghcnd-stations.txt"), encoding="utf-8"):
        if ln.startswith("C"):
            pos[ln[:11]] = (float(ln[12:20]), float(ln[21:30]))
    adm2 = gpd.read_file(os.path.join(DATOS, "procesados", "unidades.gpkg"), layer="adm2")
    adm2 = adm2[adm2.iso3 == "COL"]
    fin, _ = imerg(2)
    res = []
    for est in ultimas:
        lat, lon = pos[est]
        u = adm2[adm2.contains(Point(lon, lat))]
        if u.empty or u.unidad_id.iloc[0] not in fin:
            continue
        d = pd.read_csv(os.path.join(GHCN, est + ".csv"), usecols=["DATE", "PRCP"], dtype={"DATE": str}).dropna()
        d["mes"] = d.DATE.str[:7]
        g = d.groupby("mes").PRCP.agg(["sum", "count"])
        # mes valido de estacion: al menos 25 dias con dato; PRCP viene en decimas de mm
        g = g[(g["count"] >= 25) & (g.index >= "2000-01") & (g.index <= "2024-12")]
        s_un = fin[u.unidad_id.iloc[0]]
        tot = {m: row["sum"] / 10.0 / pd.Period(m).days_in_month for m, row in g.iterrows() if m in s_un}
        an_e, an_s = [], []
        for m in tot:
            ce = [tot[k] for k in tot if k[5:] == m[5:]]
            cs = [s_un[k] for k in tot if k[5:] == m[5:]]
            if len(ce) >= 5 and st.mean(ce) > 0 and st.mean(cs) > 0:
                an_e.append(tot[m] / st.mean(ce))
                an_s.append(s_un[m] / st.mean(cs))
        if len(an_e) >= 60:
            res.append({"estacion": est, "unidad": u.unidad_id.iloc[0], "n_meses": len(an_e),
                        "r_pearson_razones": float(np.corrcoef(an_e, an_s)[0, 1])})
    return res


def enso_vs_lluvia(fin_col, pw, o, r):
    # regresion lineal de la razon mensual (Final, 2000-2025) sobre el indice ENSO de la estacion centrada en el mes
    # ene con DJF, feb con JFM (CPC rotula con el anio del mes central); solo para saber si ENSO explica el 2026
    out = {}
    for mes_cal, est in (("01", "DJF"), ("02", "JFM")):
        for nombre, serie in (("IMERG_Final", fin_col), ("POWER", pw)):
            v = {a: serie[f"{a}-{mes_cal}"] for a in range(2000, 2026) if f"{a}-{mes_cal}" in serie}
            mu = st.mean(v.values())
            for ind, idx in (("ONI", o), ("RONI", r)):
                x = np.array([idx[f"{est} {a}"] for a in v])
                y = np.array([v[a] / mu for a in v])
                b, a0 = np.polyfit(x, y, 1)
                res = y - (a0 + b * x)
                x26 = idx[f"{est} 2026"]
                out[f"{nombre}_{mes_cal}_{ind}"] = {"n": len(x), "r": float(np.corrcoef(x, y)[0, 1]), "pendiente": float(b),
                    "indice_2026": x26, "razon_prevista_2026": float(a0 + b * x26), "sd_residuo": float(res.std(ddof=2))}
    return out


def main():
    fin0, late0 = imerg(0)
    a0 = anomalias_unidad(fin0["COL-ADM0"], late0["COL-ADM0"])
    fin1, late1 = imerg(1)
    n1 = {}
    for mes in MESES_HALLAZGO:
        r = [anomalias_unidad(fin1[u], late1[u])[mes]["razon"] for u in late1 if u in fin1 and mes in late1[u]]
        n1[mes] = {"n_unidades_adm1": len(r), "mediana_razon": st.median(r), "min": min(r), "max": max(r),
                   "unidades_con_razon_mayor_2": sum(x > 2 for x in r)}
    npts, pw, pw_series = power_colombia()
    pw_an = {}
    for mes in sorted(m for m in pw if "2025-10" <= m <= "2026-09"):
        c = [pw[f"{a}-{mes[5:]}"] for a in range(2000, 2026) if f"{a}-{mes[5:]}" in pw]
        pw_an[mes] = {"power_mm_dia": pw[mes], "clim_mm_dia": st.mean(c), "razon": pw[mes] / st.mean(c),
                      "z": (pw[mes] - st.mean(c)) / st.stdev(c), "n_clim": len(c)}
    pp = {}
    for mes in MESES_HALLAZGO:
        rr = []
        for s in pw_series:
            c = [s[f"{a}-{mes[5:]}"] for a in range(2000, 2026) if f"{a}-{mes[5:]}" in s]
            if mes in s and len(c) > 20 and st.mean(c) > 0:
                rr.append(s[mes] / st.mean(c))
        pp[mes] = {"n_puntos": len(rr), "mediana_razon": st.median(rr), "puntos_con_razon_mayor_2": sum(x > 2 for x in rr)}
    o = indice_cpc("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", 3)
    r = indice_cpc("https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt", 2)
    ultimas = ghcn_ultima_fecha()
    salida = {
        "fecha": date.today().isoformat(),
        "imerg_colombia_adm0_late_frente_a_final": a0,
        "imerg_adm1_ene_feb_2026": n1,
        "power": {"parametro": "PRECTOTCORR (MERRA-2 corregido con observaciones)", "puntos_1grado_en_colombia": npts,
                  "anomalia_colombia": pw_an, "por_punto": pp},
        "enso": {"ONI": {k: v for k, v in o.items() if k.split()[1] in ("2025", "2026")},
                 "RONI": {k: v for k, v in r.items() if k.split()[1] in ("2025", "2026")}},
        "enso_vs_lluvia": enso_vs_lluvia(fin0["COL-ADM0"], pw, o, r),
        "ghcn_ultima_fecha_prcp_por_estacion": ultimas,
        "ghcn_vs_imerg_final_adm2": ghcn_vs_imerg_final(ultimas),
    }
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=1, ensure_ascii=False)
    print("escrito", SALIDA)


if __name__ == "__main__":
    main()
