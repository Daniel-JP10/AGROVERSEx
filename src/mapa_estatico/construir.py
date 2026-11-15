# asistido por SI: Claude Code, convierte las series mensuales csv.gz en archivos estáticos para el globo (T-D9, contratos/web_datos.md v0)
"""Una matriz por variable y nivel: filas = unidades, columnas = meses 2000-01 a 2026-11.

Valores en la unidad del producto (nunca convertidos); la unidad, el producto, la versión y el
estado van por mes porque IMERG Final (mm/hr) y Late (mm/day) se empalman en 2025-10.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import pandas as pd

MES0 = (2000, 1)
N_MESES = 26 * 12 + 11  # 2000-01 .. 2026-11, igual que tiempo/valor.ts
# id de la capa del globo -> (variable del contrato, archivos de la ponderación por área)
VARIABLES = {
    "precip": ("precipitacion", ["precipitacion_final", "precipitacion_late"]),
    "t2m": ("t2m", ["t2m"]),
    "sm_raiz": ("humedad_radicular", ["humedad_radicular"]),
    "ndvi": ("ndvi", ["ndvi"]),
}
# El csv trae U+FFFD donde iba la tilde (hallazgo de T-D2): se repone solo aquí, sin tocar la fuente
CORRECCION_TEXTO = {"rean\ufffdlisis": "reanálisis"}


def indice_mes(mes: str) -> int:
    a, m = int(mes[:4]), int(mes[5:7])
    return (a - MES0[0]) * 12 + m - MES0[1]


def mes_a_texto(i: int) -> str:
    a, m = divmod(MES0[0] * 12 + (MES0[1] - 1) + int(i), 12)
    return f"{a:04d}-{m + 1:02d}"


def _texto(s: str) -> str:
    for mal, bien in CORRECCION_TEXTO.items():
        s = s.replace(mal, bien)
    if "\ufffd" in s:
        raise ValueError(f"texto con carácter de reemplazo sin corregir: {s!r}")
    return s


def _cargar(carpeta: Path, archivos: list[str]) -> pd.DataFrame:
    partes = [
        pd.read_csv(
            carpeta / f"serie_mensual_{a}_area.csv.gz",
            encoding="utf-8",
            dtype={"version": str, "unidad": str},
        )
        for a in archivos
    ]
    d = pd.concat(partes, ignore_index=True)
    d["i"] = d["mes"].map(indice_mes)
    if d["i"].min() < 0 or d["i"].max() >= N_MESES:
        raise ValueError("mes fuera del eje 2000-01 a 2026-11")
    if d.duplicated(["unidad_id", "i"]).any():
        raise ValueError("unidad y mes repetidos entre archivos (Final y Late no deben traslaparse)")
    return d


def matriz(d: pd.DataFrame, nivel: int, var_capa: str) -> dict:
    d = d[d["nivel"] == nivel]
    ids = sorted(d["unidad_id"].unique())
    pos = {u: k for k, u in enumerate(ids)}
    # unidad, producto, versión y estado deben ser únicos por mes: si no, no se puede guardar por mes
    cols = ["producto", "version", "unidad", "estado"]
    if (d.groupby("i")[cols].nunique() > 1).any().any():
        raise ValueError("un mes trae más de un producto, versión, unidad o estado")
    primero = d.groupby("i")[cols].first()
    productos: list[dict] = []
    producto_mes = [-1] * N_MESES
    for i, f in primero.iterrows():
        p = {
            "producto": _texto(str(f["producto"])),
            "version": str(f["version"]),
            "unidad": str(f["unidad"]),
            "estado": str(f["estado"]),
        }
        if p not in productos:
            productos.append(p)
        producto_mes[int(i)] = productos.index(p)
    sal = {k: [[None] * N_MESES for _ in ids] for k in ("valor", "p10", "p90", "frac")}
    cifras = {"valor": 6, "p10": 5, "p90": 5}
    for fila in d.itertuples(index=False):
        r, c = pos[fila.unidad_id], int(fila.i)
        for col, cif in cifras.items():
            v = getattr(fila, col)
            if pd.notna(v):
                sal[col][r][c] = float(f"{v:.{cif}g}")
        if pd.notna(fila.frac_valida):
            sal["frac"][r][c] = round(float(fila.frac_valida), 3)
    return {
        "formato": "web_datos v0",
        "variable": var_capa,
        "nivel": nivel,
        "ponderacion": "area",
        "mes0": "2000-01",
        "n_meses": N_MESES,
        "ids": ids,
        "productos": productos,
        "producto_mes": producto_mes,
        "tipo_rango": "espacial",
        **sal,
    }


def escribir_gz(ruta: Path, obj) -> int:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0: dos corridas dan los mismos bytes
    with open(ruta, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, compresslevel=9) as z:
        z.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    return ruta.stat().st_size


def _escribir_json_lf(ruta: Path, obj, indent: int | None = 1) -> int:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, indent=indent).replace("\r\n", "\n") + "\n"
    ruta.write_bytes(txt.encode("utf-8"))
    return ruta.stat().st_size


def construir_series(carpeta: Path, salida: Path, pais: str) -> dict:
    tam = {}
    meta = {
        "formato": "web_datos v0 (borrador, lo congela Daniel)",
        "pais": pais,
        "mes0": "2000-01",
        "n_meses": N_MESES,
        "variables": {},
    }
    for cid, (_var, archivos) in VARIABLES.items():
        d = _cargar(carpeta, archivos)
        niveles = sorted(int(n) for n in d["nivel"].unique())
        m = {}
        for nivel in niveles:
            m = matriz(d, nivel, cid)
            tam[f"{pais}/{cid}_{nivel}.json.gz"] = escribir_gz(salida / pais / f"{cid}_{nivel}.json.gz", m)
        idx = [i for i, pm in enumerate(m.get("producto_mes", [])) if pm >= 0]
        meta["variables"][cid] = {
            "niveles": niveles,
            "meses_disponibles": {
                "desde": mes_a_texto(idx[0]) if idx else None,
                "hasta": mes_a_texto(idx[-1]) if idx else None,
                "n_meses_con_producto": len(idx),
            },
            "productos": m.get("productos", []),
        }
    _escribir_json_lf(salida / "meta.json", meta)
    return tam


def construir_geo(gpkg: Path, salida: Path) -> int:
    """id -> [oeste, sur, este, norte, padre_id] (más punto lon, lat si el bbox cruza el antimeridiano)."""
    import pyogrio
    out = {}
    for capa in ("adm0", "adm1", "adm2"):
        t = pyogrio.read_dataframe(gpkg, layer=capa, read_geometry=False)
        for r in t.itertuples(index=False):
            if r.nivel_real not in (capa.upper(), "DISP"):
                continue  # repite un nivel superior: no es unidad de este nivel (contratos/unidades.md)
            padre = None if pd.isna(r.padre_id) or r.padre_id == "cruce_ambiguo" else r.padre_id
            f = [round(r.bbox_oeste, 3), round(r.bbox_sur, 3), round(r.bbox_este, 3), round(r.bbox_norte, 3), padre]
            if r.bbox_oeste <= -179.9 and r.bbox_este >= 179.9:
                f += [round(r.punto_lon, 3), round(r.punto_lat, 3)]
            out[r.unidad_id] = f
    return escribir_gz(salida / "unidades_geo.json.gz", out)


def copiar_lotes(lotes: Path, salida: Path) -> int:
    """Copia datos/lotes/lotes_demo.json a salida/lotes_demo.json (D-027)."""
    contenido = json.loads(lotes.read_text(encoding="utf-8"))
    if not isinstance(contenido.get("lotes"), list) or not contenido["lotes"]:
        raise ValueError("lotes_demo.json debe contener una lista no vacía en 'lotes'")
    salida.mkdir(parents=True, exist_ok=True)
    raw = lotes.read_bytes().replace(b"\r\n", b"\n")
    destino = salida / "lotes_demo.json"
    destino.write_bytes(raw)
    return destino.stat().st_size

# origen (relativo a AGROVERSEX_DATOS) -> destino (relativo al build): las rutas que piden globo/config.ts
ARCHIVOS_DESPLIEGUE = {
    "teselas/adm0.pmtiles": "teselas/adm0.pmtiles",
    "teselas/adm1.pmtiles": "teselas/adm1.pmtiles",
    "teselas/adm2.pmtiles": "teselas/adm2.pmtiles",
    "indice_busqueda.json.gz": "teselas/indice_busqueda.json.gz",
}


class ErrorDespliegue(RuntimeError):
    """El despliegue no puede seguir: falta algo que el build público necesita."""


def raiz_datos(entorno=None) -> Path:
    """AGROVERSEX_DATOS con teselas, índice y unidades.gpkg; si falta algo, error claro (D-037 C2.2)."""
    ruta = (os.environ if entorno is None else entorno).get("AGROVERSEX_DATOS")
    if not ruta:
        raise ErrorDespliegue("falta la variable AGROVERSEX_DATOS (carpeta datos/procesados con teselas/, indice_busqueda.json.gz y unidades.gpkg)")
    raiz = Path(ruta)
    if not raiz.is_dir():
        raise ErrorDespliegue(f"AGROVERSEX_DATOS apunta a una carpeta que no existe: {raiz}")
    faltan = [o for o in (*ARCHIVOS_DESPLIEGUE, "unidades.gpkg") if not (raiz / o).is_file() or (raiz / o).stat().st_size == 0]
    if faltan:
        raise ErrorDespliegue(f"en {raiz} faltan o están vacíos: {', '.join(faltan)}")
    return raiz


def desplegar(dist: Path, entorno=None) -> dict:
    """Copia teselas e índice a dist/ y construye dist/datos/unidades_geo.json.gz (D-033e: no se versionan)."""
    raiz = raiz_datos(entorno)
    if not dist.is_dir():
        raise ErrorDespliegue(f"no existe {dist}: corre primero npm run build en src/web")
    tam = {}
    for origen, destino in ARCHIVOS_DESPLIEGUE.items():
        (dist / destino).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(raiz / origen, dist / destino)
        tam[destino] = (dist / destino).stat().st_size
        if tam[destino] != (raiz / origen).stat().st_size:
            raise ErrorDespliegue(f"copia incompleta de {origen}")
    tam["datos/unidades_geo.json.gz"] = construir_geo(raiz / "unidades.gpkg", dist / "datos")
    return tam


def construir_manifiesto(
    salida: Path,
    version_contrato: str = "web_datos v0",
    generado_utc: str | None = None,
) -> dict:
    """Genera salida/manifiesto.json con sha256, variables, meses disponibles y fecha UTC (T-D7 Parte C)."""
    fecha_utc = generado_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta_ruta = salida / "meta.json"
    meta = json.loads(meta_ruta.read_text(encoding="utf-8")) if meta_ruta.exists() else {}
    pais = meta.get("pais", "COL")
    variables_info = {}
    for cid, info in meta.get("variables", {}).items():
        meses_disp = info.get("meses_disponibles")
        if not meses_disp:
            niv = info.get("niveles", [0])[0]
            r_gz = salida / pais / f"{cid}_{niv}.json.gz"
            if r_gz.exists():
                m = json.loads(gzip.open(r_gz, "rt", encoding="utf-8").read())
                idx = [i for i, pm in enumerate(m.get("producto_mes", [])) if pm >= 0]
                meses_disp = {
                    "desde": mes_a_texto(idx[0]) if idx else None,
                    "hasta": mes_a_texto(idx[-1]) if idx else None,
                    "n_meses_con_producto": len(idx),
                }
        variables_info[cid] = {
            "niveles": info.get("niveles", []),
            "meses_disponibles": meses_disp,
            "productos": info.get("productos", []),
        }
    archivos = {}
    for p in sorted(salida.rglob("*"), key=lambda x: x.relative_to(salida).as_posix()):
        if not p.is_file() or p.name == "manifiesto.json":
            continue
        rel = p.relative_to(salida).as_posix()
        b = p.read_bytes()
        archivos[rel] = {
            "bytes": len(b),
            "sha256": hashlib.sha256(b).hexdigest(),
        }
    manifiesto = {
        "version_contrato": version_contrato,
        "generado_utc": fecha_utc,
        "paises": [pais],
        "mes0": meta.get("mes0", "2000-01"),
        "n_meses": meta.get("n_meses", N_MESES),
        "variables": variables_info,
        "total_bytes": sum(f["bytes"] for f in archivos.values()),
        "archivos": archivos,
    }
    _escribir_json_lf(salida / "manifiesto.json", manifiesto)
    return manifiesto


def principal():
    p = argparse.ArgumentParser()
    p.add_argument("--desplegar", type=Path, metavar="DIST", help="copia teselas e índice a DIST (src/web/dist) desde AGROVERSEX_DATOS")
    p.add_argument("--series", type=Path)
    p.add_argument("--gpkg", type=Path)
    p.add_argument("--lotes", type=Path)
    p.add_argument("--salida", type=Path)
    p.add_argument("--pais", default="COL")
    p.add_argument("--generado-utc", default=None)
    a = p.parse_args()
    if a.desplegar:
        try:
            print(json.dumps(desplegar(a.desplegar), indent=1))
        except ErrorDespliegue as e:
            sys.exit(f"ERROR de despliegue: {e}")
        return
    if not (a.series and a.salida):
        p.error("--series y --salida son obligatorios si no se usa --desplegar")
    tam = construir_series(a.series, a.salida, a.pais)
    if a.gpkg:
        tam["unidades_geo.json.gz"] = construir_geo(a.gpkg, a.salida)
    if a.lotes:
        tam["lotes_demo.json"] = copiar_lotes(a.lotes, a.salida)
    man = construir_manifiesto(a.salida, generado_utc=a.generado_utc)
    tam["manifiesto.json"] = (a.salida / "manifiesto.json").stat().st_size
    print(json.dumps(tam, indent=1), "total MB:", round(man["total_bytes"] / 1e6, 2))


if __name__ == "__main__":
    principal()
