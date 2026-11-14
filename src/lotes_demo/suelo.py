# asistido por SI: Claude Code, parámetros de suelo por lote desde la respuesta REST de SoilGrids 2.0 (T-D5 Parte B)
import json
import sys
from pathlib import Path

FRACCION_C_MO = 0.58  # MO = COS / 0,58, igual que el Gemelo (INFERENCIA)


def media_ponderada(capa, estadistico, hasta_cm):
    # media de las capas ponderada por espesor, cortada en hasta_cm
    num = den = 0.0
    for d in capa["depths"]:
        t, b = d["range"]["top_depth"], min(d["range"]["bottom_depth"], hasta_cm)
        v = d["values"].get(estadistico)
        if b <= t or v is None:
            continue
        num += v * (b - t)
        den += b - t
    return num / den if den else None


def _tri(capas, nombre, f, hasta):
    c = capas[nombre]
    m, lo, hi = (media_ponderada(c, q, hasta) for q in ("mean", "Q0.05", "Q0.95"))
    return dict(valor=m * f, rango=[min(lo, m) * f, max(hi, m) * f])


def parametros_desde_rest(rest, lote_id, hasta_cm=100, hasta_cos=30):
    capas = {l["name"]: l for l in rest["properties"]["layers"]}
    lon, lat = rest["geometry"]["coordinates"]
    P = {}
    # g/kg -> kg/kg
    P["arena"] = dict(_tri(capas, "sand", 0.001, hasta_cm), unidad="kg/kg", etiqueta="FUENTE",
                      profundidad_cm=[0, hasta_cm])
    P["arcilla"] = dict(_tri(capas, "clay", 0.001, hasta_cm), unidad="kg/kg", etiqueta="FUENTE",
                        profundidad_cm=[0, hasta_cm])
    # cg/cm3 -> kg/dm3
    P["densidad_aparente"] = dict(_tri(capas, "bdod", 0.01, hasta_cm), unidad="kg/dm3", etiqueta="FUENTE",
                                  profundidad_cm=[0, hasta_cm])
    # dg/kg -> g/kg -> % de MO
    mo = _tri(capas, "soc", 0.1 / 10 / FRACCION_C_MO, hasta_cm)
    P["mo_pct"] = dict(mo, unidad="%", etiqueta="INFERENCIA", profundidad_cm=[0, hasta_cm],
                       metodo="MO = COS/0,58; el factor 0,58 es una convención, no una medición")
    # COS 0-30 cm = suma(SOC g/kg * BD g/cm3 * espesor cm) * 0,1, sin fragmentos gruesos
    stock = {}
    for q in ("mean", "Q0.05", "Q0.95"):
        s = 0.0
        for ds, db in zip(capas["soc"]["depths"], capas["bdod"]["depths"]):
            t, b = ds["range"]["top_depth"], min(ds["range"]["bottom_depth"], hasta_cos)
            if b > t:
                s += ds["values"][q] / 10 * db["values"][q] / 100 * (b - t) * 0.1
        stock[q] = s
    P["cos_t_ha"] = dict(valor=stock["mean"], rango=[min(stock["Q0.05"], stock["mean"]), max(stock["Q0.95"], stock["mean"])],
                         unidad="t C/ha", etiqueta="FUENTE", profundidad_cm=[0, hasta_cos],
                         metodo="suma SOC*BD*espesor; el rango combina Q0.05 de SOC con Q0.05 de BD (cota amplia)")
    # agua disponible = CC(33 kPa) - PMP(1500 kPa); unidad del producto 1e-3 cm3/cm3 = mm/m
    cc, pm = capas["wv0033"], capas["wv1500"]
    m = media_ponderada(cc, "mean", hasta_cm) - media_ponderada(pm, "mean", hasta_cm)
    lo = media_ponderada(cc, "Q0.05", hasta_cm) - media_ponderada(pm, "Q0.95", hasta_cm)
    hi = media_ponderada(cc, "Q0.95", hasta_cm) - media_ponderada(pm, "Q0.05", hasta_cm)
    P["agua_disponible_mm_m"] = dict(valor=m, rango=[max(lo, 0.0), hi], unidad="mm de agua por m de suelo",
                                     etiqueta="INFERENCIA", profundidad_cm=[0, hasta_cm],
                                     metodo="media(wv0033) - media(wv1500) de SoilGrids; rango = cota amplia "
                                            "Q0.05-Q0.95 cruzados, no son cuantiles de la diferencia")
    return dict(
        lote_id=lote_id, lat=round(lat, 3), lon=round(lon, 3), etiqueta="DEMO",
        fuente="SoilGrids 2.0 (ISRIC), API REST rest.isric.org/soilgrids/v2.0/properties/query, no rasters locales",
        licencia="CC BY 4.0 (FUENTE: Gemelo cita CC BY 4.0; verificar en ficha)", naturaleza="estimado",
        tipo_rango="Q0.05-Q0.95 de SoilGrids en el píxel de 250 m; incertidumbre del mapa, no del lote",
        archivo_soilgrids_json="soilgrids_rest.json", parametros=P)


if __name__ == "__main__":
    raiz = Path(sys.argv[1])
    for lote in ("DEMO-USA-01", "DEMO-COL-01"):
        rest = json.loads((raiz / lote / "soilgrids_rest.json").read_text())
        out = parametros_desde_rest(rest, lote)
        (raiz / lote / "parametros_suelo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
