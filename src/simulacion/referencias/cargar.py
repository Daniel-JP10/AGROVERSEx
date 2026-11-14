# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from simulacion import config

AQUI = Path(__file__).resolve().parent
EVIDENCIA = config.RAIZ / "evidencia"


def _registros(obj):
    # Todo dict con "etiqueta" es un registro de referencia
    if isinstance(obj, dict):
        if "etiqueta" in obj:
            yield obj
        for v in obj.values():
            yield from _registros(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _registros(v)


def _leer(nombre):
    datos = yaml.safe_load((AQUI / nombre).read_text(encoding="utf-8"))
    # Cada registro cita una ficha EV existente o, si no la hay, su fila en el reporte
    for reg in _registros(datos):
        fid = reg.get("fuente_id")
        if fid is not None and EVIDENCIA.exists() and not (EVIDENCIA / f"{fid}.yaml").exists():
            raise ValueError(f"{nombre}: fuente_id {fid} sin ficha en evidencia/")
        if fid is None and not reg.get("fuente_informe"):
            raise ValueError(f"{nombre}: registro sin fuente_id ni fuente_informe")
    return datos


def cargar_enso():
    # Cada fila del YAML es un año; sus 12 valores van en orden de mes central (Ene..Dic)
    datos = _leer("enso.yaml")
    df = pd.DataFrame({"mes_id": np.arange(config.N_MESES)})
    for clave in ("oni", "roni"):
        serie = np.full(config.N_MESES, np.nan)
        for reg in datos[clave]:
            for mes, valor in enumerate(reg["valores"]):
                mes_id = (reg["anio"] - config.FECHA_INICIO.year) * 12 + mes
                if 0 <= mes_id < config.N_MESES and valor is not None:
                    serie[mes_id] = valor
        df[clave] = serie
    return df


def cargar_eventos():
    # Solo los de etiqueta FUENTE; los PENDIENTE no entran al generador
    eventos = _leer("eventos.yaml")["eventos"]
    cols = ["id", "tipo", "inicio", "fin", "region_texto", "magnitud_texto", "url", "etiqueta"]
    return [{c: e[c] for c in cols} for e in eventos if e["etiqueta"] == "FUENTE"]


def cargar_kluger():
    filas = _leer("kluger.yaml")["efecto_antecesor"]
    # D-009: las filas de China se rotulan y se quitan si la bandera está apagada
    if not config.INCLUIR_PROCEDENCIA_CHINA:
        filas = [f for f in filas if not f["procedencia_china"]]
    cols = ["pais", "antecesor", "cultivo", "efecto2", "eff_div", "beta_lluvia", "beta_t",
            "sig_efecto2", "sig_eff_div", "sig_beta_lluvia", "sig_beta_t",
            "procedencia_china", "fuente_id"]
    return pd.DataFrame(filas, columns=cols)


def cargar_fao56():
    filas = _leer("fao56.yaml")["cultivos"]
    cols = ["cultivo", "kc_ini", "kc_mid", "kc_end", "etapas", "zr_min", "zr_max", "p",
            "agua_min", "agua_max", "etiqueta", "etiqueta_agua", "fuente_id"]
    return pd.DataFrame(filas, columns=cols)


def cargar_faostat():
    cols = ["pais", "cultivo", "periodo", "media", "minimo", "maximo", "etiqueta", "fuente_id"]
    return pd.DataFrame(_leer("faostat.yaml")["rendimientos"], columns=cols)


def cargar_teleconexiones():
    filas = _leer("teleconexiones.yaml")["teleconexiones"]
    df = pd.DataFrame([f for f in filas if f["estado"].startswith("2 fuentes")])
    # coef queda NULL: la magnitud, cuando existe, va en coef_mm_dia (Cai 2025)
    df["coef"] = np.nan
    for c, v in (("nina_aplica", True), ("coef_mm_dia", None), ("meses_coef", None)):
        if c not in df:
            df[c] = v
    df["nina_aplica"] = df["nina_aplica"].map(lambda v: True if pd.isna(v) else bool(v))
    return df[["macroregion", "temporada", "variable", "signo_nino", "signo_nina", "coef", "fuentes", "estado",
               "nina_aplica", "coef_mm_dia", "meses_coef", "fuente_informe"]]


def cargar_berkeley():
    # Tasa 2000-2020 en °C por década; INFERENCIA propia sobre datos CC BY-NC (D-003)
    return {r["region"]: r["tasa_2000_2020"] for r in _leer("berkeley.yaml")["regiones"]}


def cargar_gistemp_anual():
    filas = _leer("gistemp.yaml")["anual"]
    return pd.Series({r["anio"]: r["loti"] for r in filas}, name="loti", dtype=float)


def cargar_gistemp_tendencia():
    return _leer("gistemp.yaml")["tendencia_estaciones"]


def cargar_rodell():
    # Gt/año y, desde R-1b, área y cm/año = Gt/año / km² * 1e5 (INFERENCIA); caja = SUPUESTO (lat_s, lat_n, lon_o, lon_e)
    cols = ["region", "gt_anio", "incertidumbre", "causa", "area_km2", "cm_anio", "hielo", "caja",
            "etiqueta", "etiqueta_cm", "fuente_id"]
    return pd.DataFrame(_leer("rodell.yaml")["regiones"], columns=cols)


def cargar_sistemas_rotacion():
    return pd.DataFrame(_leer("sistemas_rotacion.yaml")["sistemas"])


def cargar_sucesion():
    return pd.DataFrame(_leer("sucesion.yaml")["reglas"])
