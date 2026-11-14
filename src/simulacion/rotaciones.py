# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Tablas de referencia de rotación de cultivos (Task 9, INICIAR §11).

Cada función devuelve filas como tuplas en el orden de columnas de esquema_agroversex.sql, listas para executemany.
Regla general: un valor numérico o un texto de estrategia se guarda solo si su fuente tiene ficha en
evidencia/ (EV-*). Sin ficha, el valor numérico queda NULL y la etiqueta sale PENDIENTE (AGENTS §4, 15.2-I).
"""
import pandas as pd

from simulacion import config
from simulacion.referencias.cargar import cargar_fao56, cargar_kluger, cargar_sistemas_rotacion, cargar_sucesion

# Decisión 15.2-H pendiente del director: sin ella no se crean filas de coberturas análogas
DECISION_15_2_H = None

# Ficha de agua de FAO-56 (INV-ROT §3). cargar_fao56 no devuelve fuente_agua, así que va fija aquí
FICHA_AGUA_FAO = "EV-ROT-011"
# Hernia de las crucíferas: R1 da 7 años y R2 da 4 para colza; EV-ROT-016 recoge ambas cifras
FICHA_HERNIA = "EV-ROT-016"
CLIMA_SUCESION = "templado; trópico: intervalo PENDIENTE, revisión local"
CONTRASTE = "contraste, no rotación"


def _ficha_existe(fid):
    if fid is None:
        return False
    evidencia = config.RAIZ / "evidencia"
    return not evidencia.exists() or (evidencia / f"{fid}.yaml").exists()


def _valor(v):
    # np.int64 o np.float64 a tipo nativo; NaN a None
    if v is None or pd.isna(v):
        return None
    return v.item() if hasattr(v, "item") else v


def _con_ficha(fid, v):
    # Sin ficha EV, el valor es NULL aunque la referencia lo traiga
    return _valor(v) if _ficha_existe(fid) else None


def _texto(t):
    # Lo que la referencia marca PENDIENTE no se muestra como estrategia
    return None if t is None or "PENDIENTE" in t else t


def _significativo(f):
    # Kluger trae cuatro banderas sig_*; el esquema tiene una sola columna significativo.
    # Máscara: bit 0 efecto2, bit 1 eff_div, bit 2 beta_lluvia, bit 3 beta_t (1 = significativo).
    return (int(f["sig_efecto2"]) | int(f["sig_eff_div"]) << 1
            | int(f["sig_beta_lluvia"]) << 2 | int(f["sig_beta_t"]) << 3)


def filas_sistema_rotacion():
    filas = []
    for r in cargar_sistemas_rotacion().to_dict("records"):
        region = r["region"]
        fid = r["fuente_id"]
        # FUENTE o INFERENCIA solo con ficha; lo demás queda PENDIENTE
        etiqueta = r["etiqueta"] if r["etiqueta"] in ("FUENTE", "INFERENCIA") and _ficha_existe(fid) else "PENDIENTE"
        habitual = _texto(r["habitual"])
        if r["region"] == "Pampa":
            # INICIAR §11.2: dos rotaciones reales y un contraste (monocultivo), en filas separadas
            filas.append((r["region"], region, habitual, _texto(r["alternativa_2"]), None, fid, etiqueta))
            filas.append((f"{r['region']} contraste", region, _texto(r["alternativa_1"]), CONTRASTE, None,
                          fid, "PENDIENTE"))
            continue
        filas.append((r["region"], region, habitual, _texto(r["alternativa_1"]), _texto(r["alternativa_2"]),
                      fid, etiqueta))
    return filas


def filas_efecto_antecesor():
    filas = []
    for f in cargar_kluger().to_dict("records"):
        pais = f["pais"]
        fid = f["fuente_id"]
        filas.append((pais, f["antecesor"], f["cultivo"],
                      _con_ficha(fid, f["efecto2"]), _con_ficha(fid, f["eff_div"]),
                      _con_ficha(fid, f["beta_lluvia"]), _con_ficha(fid, f["beta_t"]),
                      _significativo(f), fid))
    return filas


def filas_cultivo():
    filas = []
    for c in cargar_fao56().to_dict("records"):
        agua_ok = c["etiqueta_agua"] == "FUENTE" and _ficha_existe(FICHA_AGUA_FAO)
        fid = c["fuente_id"]
        kc_ok = _ficha_existe(fid)
        etiqueta = "FUENTE" if agua_ok else "FUENTE; agua PENDIENTE"
        filas.append((c["cultivo"], c["cultivo"], None,
                      _con_ficha(fid, c["kc_ini"]), _con_ficha(fid, c["kc_mid"]), _con_ficha(fid, c["kc_end"]),
                      _con_ficha(fid, c["etapas"]), _con_ficha(fid, c["zr_min"]), _con_ficha(fid, c["zr_max"]),
                      _con_ficha(fid, c["p"]),
                      _valor(c["agua_min"]) if agua_ok else None, _valor(c["agua_max"]) if agua_ok else None,
                      None, None, None, None,
                      fid if kc_ok else None,
                      etiqueta if kc_ok else "PENDIENTE"))
    return filas


def filas_regla_sucesion():
    filas = []
    hernia = []
    for r in cargar_sucesion().to_dict("records"):
        if r["enfermedad"] == "Hernia":
            hernia.append(r)  # se unen en una fila de rango
            continue
        fid = r["fuente_id"]
        filas.append((r["cultivo_o_familia"], r["enfermedad"],
                      _con_ficha(fid, r["intervalo_min"]), _con_ficha(fid, r["intervalo_max"]),
                      CLIMA_SUCESION, fid))
    # Brásicas con hernia: 4 a 7 años como rango, no promedio (INICIAR §11.6)
    fila_hernia = ("Brásicas (incluye colza)", "Hernia",
                   _con_ficha(FICHA_HERNIA, min(r["intervalo_min"] for r in hernia)),
                   _con_ficha(FICHA_HERNIA, max(r["intervalo_max"] for r in hernia)),
                   CLIMA_SUCESION, FICHA_HERNIA)
    filas.append(fila_hernia)
    return filas
