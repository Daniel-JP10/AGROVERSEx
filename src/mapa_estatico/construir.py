# asistido por SI: Claude Code (Anthropic), convierte las series mensuales csv.gz en archivos estáticos para el globo (T-D9, contratos/web_datos.md v0)
"""Una matriz por variable y nivel: filas = unidades, columnas = meses 2000-01 a 2026-11.

Valores en la unidad del producto (nunca convertidos); la unidad, el producto, la versión y el
estado van por mes porque IMERG Final (mm/hr) y Late (mm/day) se empalman en 2025-10.
"""
import argparse
from datetime import datetime, timezone
import getpass
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
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
# H-F3-1: la app va en inglés; el nombre del producto se traduce aquí, nunca a mano en meta.json
PRODUCTO_EN = {
    "GPM IMERG Final Run, mensual 0,1 grados (GPM_3IMERGM)": "GPM IMERG Final Run, monthly 0.1° (GPM_3IMERGM)",
    "GPM IMERG Late Run, diario agregado a mes en UTC (GPM_3IMERGDL)": "GPM IMERG Late Run, daily aggregated to month in UTC (GPM_3IMERGDL)",
    "MERRA-2 reanálisis, M2TMNXSLV (T2M)": "MERRA-2 reanalysis, M2TMNXSLV (T2M)",
    "MODIS Terra MOD13C2 NDVI mensual 0,05 grados": "MODIS Terra MOD13C2 NDVI, monthly 0.05°",
    "GLDAS Noah 0,25 mensual, MODELO de superficie terrestre (GLDAS_NOAH025_M, RootMoist_inst)": "GLDAS Noah 0.25° monthly, land surface MODEL (GLDAS_NOAH025_M, RootMoist_inst)",
}


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
    return PRODUCTO_EN.get(s, s)


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


# Series del mundo (S1, traspaso S1w): se escriben al desplegar en dist/datos, no se versionan
# Sufijo del archivo por ponderación: área conserva el nombre de v0 y cultivo lleva _cultivo
PONDERACIONES = {"area": "", "cultivo": "_cultivo"}
MUNDO = "MUNDO"  # adm0 y adm1 de todos los países van en un archivo por variable; adm2 va por país
_COLS_MUNDO = {
    "unidad_id": "category", "nivel": "int8", "mes": "category", "valor": "float32", "p10": "float32", "p90": "float32",
    "frac_valida": "float32", "producto": "category", "version": "category", "estado": "category", "unidad": "category", "motivo": "category",
}


def _leer_mundo(carpeta: Path, archivos: list[str], pond: str) -> pd.DataFrame:
    partes = [pd.read_csv(carpeta / f"serie_mensual_{a}_{pond}.csv.gz", usecols=list(_COLS_MUNDO), dtype=_COLS_MUNDO, encoding="utf-8") for a in archivos]
    if len(partes) == 1:
        return partes[0]
    # Final y Late traen categorías distintas: se unen para no volver a texto (memoria)
    d = {}
    for col, tipo in _COLS_MUNDO.items():
        if tipo == "category":
            d[col] = pd.api.types.union_categoricals([p[col] for p in partes], sort_categories=True)
        else:
            d[col] = pd.concat([p[col] for p in partes], ignore_index=True)
    return pd.DataFrame(d)


def _filas_json(m, fmt: str) -> str:
    # NaN es null; formato fijo de cifras significativas (6 en valor, 5 en p10 y p90, 3 en frac)
    return "[" + ",".join("[" + ",".join("null" if v != v else format(v, fmt) for v in fila) + "]" for fila in m.tolist()) + "]"


def _trabajo_mundo(args) -> dict:
    """Una variable y una ponderación: escribe MUNDO/<cid>_<0|1><suf>.json.gz y <ISO3>/<cid>_2<suf>.json.gz."""
    import numpy as np
    carpeta, salida, cid, archivos, pond, adm2_paises = args
    suf = PONDERACIONES[pond]
    d = _leer_mundo(Path(carpeta), archivos, pond)
    if d["unidad_id"].cat.categories.str.contains("�").any():
        raise ValueError("unidad_id con carácter de reemplazo")
    meses = d["mes"].cat.categories
    i = np.array([indice_mes(m) for m in meses], dtype=np.int32)[d["mes"].cat.codes.to_numpy()]
    if i.min() < 0 or i.max() >= N_MESES:
        raise ValueError("mes fuera del eje 2000-01 a 2026-11")
    uc = d["unidad_id"].cat.codes.to_numpy().astype(np.int64)
    if len(np.unique(uc * N_MESES + i)) != len(uc):
        raise ValueError("unidad y mes repetidos entre archivos (Final y Late no deben traslaparse)")
    # producto, versión, unidad y estado únicos por mes (como en matriz)
    cols = ["producto", "version", "unidad", "estado"]
    # códigos de categoría, no texto: pasar 17 millones de filas a str tardaba minutos y llenaba la memoria
    pm_df = pd.DataFrame({c: d[c].cat.codes.to_numpy() for c in cols}).assign(i=i).drop_duplicates()
    for c in cols:
        pm_df[c] = np.asarray(d[c].cat.categories, dtype=object)[pm_df[c].to_numpy()]
    if pm_df["i"].duplicated().any():
        raise ValueError("un mes trae más de un producto, versión, unidad o estado")
    productos: list[dict] = []
    producto_mes = [-1] * N_MESES
    for f in pm_df.sort_values("i").itertuples(index=False):
        p = {"producto": _texto(f.producto), "version": f.version, "unidad": f.unidad, "estado": f.estado}
        if p not in productos:
            productos.append(p)
        producto_mes[int(f.i)] = productos.index(p)
    cats = np.asarray(d["unidad_id"].cat.categories, dtype=object)
    iso = np.array([c.split("-")[0] for c in cats], dtype=object)
    nivel = d["nivel"].to_numpy()
    sin_c = (d["motivo"] == "sin_cultivo").to_numpy()
    vals = {k: d[k].to_numpy() for k in ("valor", "p10", "p90", "frac_valida")}
    fmts = {"valor": ".6g", "p10": ".5g", "p90": ".5g", "frac_valida": ".3g"}
    sal = Path(salida)
    tam, cuenta = {}, {}

    def escribir(filas, n: int, ruta: str):
        cod = uc[filas]
        ids_cod = np.unique(cod)  # categorías ordenadas: ids en orden alfabético, como en matriz
        r, c = np.searchsorted(ids_cod, cod), i[filas]
        mats = {}
        for k in vals:
            m = np.full((len(ids_cod), N_MESES), np.nan, dtype=np.float32)
            m[r, c] = vals[k][filas]
            mats[k] = m
        # Sin cultivo en todos sus meses: la app dice "No cropland", nunca 0
        n_sc, n_tot = np.bincount(r, weights=sin_c[filas], minlength=len(ids_cod)), np.bincount(r, minlength=len(ids_cod))
        sin_cultivo = [str(x) for x in cats[ids_cod[(n_sc == n_tot) & (n_tot > 0)]]]
        cab = {
            "formato": "web_datos v0", "variable": cid, "nivel": n, "ponderacion": pond, "mes0": "2000-01", "n_meses": N_MESES,
            "ids": [str(x) for x in cats[ids_cod]], "productos": productos, "producto_mes": producto_mes, "tipo_rango": "espacial",
            "sin_cultivo": sin_cultivo,
        }
        txt = json.dumps(cab, ensure_ascii=False, separators=(",", ":"))[:-1]
        txt += "".join(f',"{k}":{_filas_json(mats[k0], fmts[k0])}' for k, k0 in (("valor", "valor"), ("p10", "p10"), ("p90", "p90"), ("frac", "frac_valida"))) + "}"
        dest = sal / ruta
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, compresslevel=6) as z:
            z.write(txt.encode("utf-8"))
        tam[ruta] = dest.stat().st_size
        con_valor = int((~np.isnan(mats["valor"])).any(axis=1).sum())
        a = cuenta.setdefault(str(n), {"ids": 0, "con_valor": 0, "sin_cultivo": 0, "archivos": 0})
        a["ids"] += len(ids_cod); a["con_valor"] += con_valor; a["sin_cultivo"] += len(sin_cultivo); a["archivos"] += 1

    for n in (0, 1):
        escribir(np.flatnonzero(nivel == n), n, f"{MUNDO}/{cid}_{n}{suf}.json.gz")
    filas2 = np.flatnonzero(nivel == 2)
    por_pais = pd.Series(filas2).groupby(iso[uc[filas2]]).indices
    for p, pos in sorted(por_pais.items()):
        if adm2_paises is None or p in adm2_paises:
            escribir(filas2[pos], 2, f"{p}/{cid}_2{suf}.json.gz")
    idx = [k for k, x in enumerate(producto_mes) if x >= 0]
    return {
        "cid": cid, "pond": pond, "tam": tam, "cuenta": cuenta, "productos": productos,
        "paises": sorted(set(iso[np.unique(uc[nivel == 0])])), "adm2": sorted(p for p in por_pais if adm2_paises is None or p in adm2_paises),
        "meses": {"desde": mes_a_texto(idx[0]) if idx else None, "hasta": mes_a_texto(idx[-1]) if idx else None, "n_meses_con_producto": len(idx)},
    }


def construir_mundo(carpeta: Path, salida: Path, adm2_paises: set[str] | None = None, procesos: int = 4) -> dict:
    """Series de S1 de todos los países con las dos ponderaciones y meta.json con los países con dato."""
    from concurrent.futures import ProcessPoolExecutor
    trabajos = [(str(carpeta), str(salida), cid, archivos, pond, adm2_paises) for cid, (_v, archivos) in VARIABLES.items() for pond in PONDERACIONES]
    faltan = [f"serie_mensual_{a}_{t[4]}.csv.gz" for t in trabajos for a in t[3] if not (carpeta / f"serie_mensual_{a}_{t[4]}.csv.gz").is_file()]
    if faltan:
        raise ErrorDespliegue(f"en {carpeta} faltan: {', '.join(faltan)}")
    if procesos > 1:
        with ProcessPoolExecutor(max_workers=procesos) as ex:
            res = list(ex.map(_trabajo_mundo, trabajos))
    else:
        res = [_trabajo_mundo(t) for t in trabajos]
    meta = {
        "formato": "web_datos v0",
        "mes0": "2000-01",
        "n_meses": N_MESES,
        "paises": sorted(set().union(*(r["paises"] for r in res))),
        "paises_adm2": sorted(set().union(*(r["adm2"] for r in res))),
        "mundo": MUNDO,
        "ponderaciones": PONDERACIONES,
        "ponderacion_defecto": "cultivo",
        "variables": {},
        "unidades_publicadas": {},
    }
    tam = {}
    for r in res:
        tam.update(r["tam"])
        meta["unidades_publicadas"].setdefault(r["cid"], {})[r["pond"]] = r["cuenta"]
        if r["pond"] == "area":
            meta["variables"][r["cid"]] = {"niveles": [0, 1, 2], "meses_disponibles": r["meses"], "productos": r["productos"]}
    tam["meta.json"] = _escribir_json_lf(salida / "meta.json", meta)
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


def _metadatos_pmtiles(contenido: bytes) -> bytes:
    """Cabecera y metadatos JSON de un PMTiles v3 (sin los datos de teselas)."""
    if contenido[:7] != b"PMTiles" or len(contenido) < 127:
        return contenido
    off, largo = int.from_bytes(contenido[24:32], "little"), int.from_bytes(contenido[32:40], "little")
    meta = contenido[off:off + largo]
    try:
        meta = gzip.decompress(meta)
    except OSError:
        pass
    return contenido[:127] + meta


# Extensiones que se leen como texto; en las demás (imágenes, binarios) no se busca la letra de unidad (V5)
TEXTO = {".js", ".mjs", ".css", ".html", ".json", ".txt", ".md", ".svg", ".map", ".xml", ".csv", ".webmanifest"}
# Rutas locales sin re.I (V5): Unix, carpetas de usuario, rutas de red y la carpeta de herramientas del despliegue
_COMUNES = r"""/home/|/Users/|/mnt/|/tmp/|/root/|/var/folders/|/opt/|\\{1,2}Users\\{1,2}|(?<=["'`\s(=])\\{2,4}[A-Za-z][A-Za-z0-9._-]+\\{1,2}[A-Za-z][A-Za-z0-9._$-]|herramientas-despliegue"""
# Letra de unidad mayúscula o minúscula (V6.2) tras inicio, comilla, espacio, ( = > o / (file:///C:/, ../C:/, V6.5),
# con /, \\ o una \ que no abra un escape \n \r \t \u (V6.6), y una carpeta de 2 o más caracteres
_UNIDAD = r"""(?<![^\s"'`(=>/])[A-Za-z]:(?:/|\\{2}|\\(?![nrtu]))[A-Za-z][A-Za-z0-9._-]+"""


def buscar_fugas(dist: Path) -> list[str]:
    """Archivos de dist con rutas locales, de red, la carpeta de herramientas o el usuario de la máquina como segmento de ruta."""
    usuario = re.escape(getpass.getuser())
    comun = re.compile(rf"{_COMUNES}|[/\\]{usuario}[/\\]")
    unidad = re.compile(_UNIDAD)
    hallazgos = []
    for p in sorted(x for x in dist.rglob("*") if x.is_file()):
        contenido, es_texto = p.read_bytes(), p.suffix.lower() in TEXTO
        if p.suffix == ".pmtiles":
            contenido, es_texto = _metadatos_pmtiles(contenido), True
        elif p.suffix == ".gz":
            try:
                contenido, es_texto = gzip.decompress(contenido), True
            except OSError:
                pass
        texto = contenido.decode("utf-8", errors="replace")
        m = comun.search(texto) or (unidad.search(texto) if es_texto else None)
        if m:
            hallazgos.append(f"{p.relative_to(dist).as_posix()}: {m.group(0)}")
    return hallazgos


# Límites de Cloudflare Pages, plan Free (developers.cloudflare.com/pages/platform/limits/, leída 2026-11-15):
# 20 000 archivos por sitio y 25 MiB por archivo. La página no fija tope total; el de 300 MB no tenía fuente (director 15:27)
MAX_ARCHIVO = 25 * 1024 * 1024
MAX_ARCHIVOS = 20_000


def revisar_limites(dist: Path, excluir: tuple[str, ...] = ("teselas/",)) -> list[str]:
    """Archivos de más de 25 MiB o 20 000 archivos o más; excluir: prefijos que van a otro alojamiento (D-040)."""
    archivos = [x for x in dist.rglob("*") if x.is_file() and not x.relative_to(dist).as_posix().startswith(excluir)]
    fallos = [f"{x.relative_to(dist).as_posix()} pesa {x.stat().st_size} B" for x in archivos if x.stat().st_size > MAX_ARCHIVO]
    if len(archivos) >= MAX_ARCHIVOS:
        fallos.append(f"{len(archivos)} archivos")
    return fallos


def desplegar(dist: Path, entorno=None, adm2_paises: set[str] | None = None) -> dict:
    """Copia teselas e índice a dist/, construye dist/datos/unidades_geo.json.gz (D-033e: no se versionan) y las series del mundo.

    adm2_paises: respaldo del director (adm2 solo de esos países, por ejemplo COL y USA); None = todos.
    """
    raiz = raiz_datos(entorno)
    env = os.environ if entorno is None else entorno
    if adm2_paises is None and env.get("AGROVERSEX_ADM2_PAISES"):
        adm2_paises = {x.strip().upper() for x in env["AGROVERSEX_ADM2_PAISES"].split(",") if x.strip()}
    if not dist.is_dir():
        raise ErrorDespliegue(f"no existe {dist}: corre primero npm run build en src/web")
    tam = {}
    limpias = (os.environ if entorno is None else entorno).get("AGROVERSEX_TESELAS")
    if limpias:
        # V5: un AGROVERSEX_TESELAS mal puesto debe fallar con un mensaje claro, no con un FileNotFoundError
        faltan = [Path(o).name for o in ARCHIVOS_DESPLIEGUE if o.endswith(".pmtiles") and not (Path(limpias) / Path(o).name).is_file()]
        if faltan:
            raise ErrorDespliegue(f"AGROVERSEX_TESELAS={limpias} no tiene {', '.join(faltan)}: debe ser la carpeta con las copias limpias de los .pmtiles")
    for origen, destino in ARCHIVOS_DESPLIEGUE.items():
        (dist / destino).parent.mkdir(parents=True, exist_ok=True)
        # AGROVERSEX_TESELAS: carpeta con las copias limpias de los .pmtiles (metadatos sin rutas internas)
        fuente = Path(limpias) / Path(origen).name if limpias and origen.endswith(".pmtiles") else raiz / origen
        shutil.copyfile(fuente, dist / destino)
        tam[destino] = (dist / destino).stat().st_size
        if tam[destino] != fuente.stat().st_size:
            raise ErrorDespliegue(f"copia incompleta de {origen}")
    tam["datos/unidades_geo.json.gz"] = construir_geo(raiz / "unidades.gpkg", dist / "datos")
    # Series del mundo (S1) desde AGROVERSEX_DATOS/series_mundo/consolidados; sin esa carpeta el build queda con COL de public/
    series = raiz / "series_mundo" / "consolidados"
    if series.is_dir():
        tam.update({f"datos/{k}": v for k, v in construir_mundo(series, dist / "datos", adm2_paises).items()})
    # Ningún archivo publicado puede llevar rutas locales ni el usuario de la máquina (director, 10:00)
    fugas = buscar_fugas(dist)
    if fugas:
        # V5: no queda un dist con fugas listo para subir por error
        shutil.rmtree(dist)
        raise ErrorDespliegue("dist contiene rutas locales o el usuario de la máquina: " + "; ".join(fugas[:10]))
    # V6.3: los límites de Pages se revisan en el mismo paso que publica
    limites = revisar_limites(dist)
    if limites:
        raise ErrorDespliegue("dist supera los límites de Pages: " + "; ".join(limites[:10]))
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
    p.add_argument("--adm2-paises", default=None, help="respaldo: adm2 solo de estos ISO3 separados por coma (por ejemplo COL,USA)")
    a = p.parse_args()
    if a.desplegar:
        try:
            import time
            t0 = time.perf_counter()
            adm2 = {x.strip().upper() for x in a.adm2_paises.split(",") if x.strip()} if a.adm2_paises else None
            tam = desplegar(a.desplegar, adm2_paises=adm2)
            print(json.dumps({k: v for k, v in tam.items() if not k.startswith("datos/") or k.count("/") < 2 or "/MUNDO/" in k}, indent=1))
            print(f"archivos: {len(tam)}, MB: {sum(tam.values()) / 1e6:.1f}, segundos: {time.perf_counter() - t0:.0f}")
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
