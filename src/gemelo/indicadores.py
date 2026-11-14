# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Indicadores del gemelo: definición matemática, unidad y cálculo por miembro del ensamble.

H = años del horizonte; las sumas son sobre todos los días salvo que se indique "días de cultivo".
"""
import numpy as np

from gemelo.clima import MES_DE_DIA

DEFINICIONES = {
    "riego_mm_anio": ("mm/año", "sum(I_bruto) / H", "Agua de riego aplicada (bruta, incluye pérdidas de aplicación)"),
    "et_real_mm_anio": ("mm/año", "sum(ETa) / H", "Agua que usan cultivo y suelo (evapotranspiración real)"),
    "drenaje_mm_anio": ("mm/año", "sum(D) / H", "Agua que se va por debajo del perfil"),
    "escorrentia_mm_anio": ("mm/año", "sum(R) / H", "Agua que escurre por la superficie"),
    "deficit_relativo": ("adimensional", "1 - sum(ETa) / sum(ETc) en días de cultivo",
                         "Cuánto le faltó de agua al cultivo frente a lo que pedía (0 = nada)"),
    "dias_estres_anio": ("días/año", "días de cultivo con Ks < 0,99, / H", "Días con estrés hídrico"),
    "lixiviacion_n_kg_ha_anio": ("kg N/ha/año", "sum(L_lix) / H", "Nitrógeno lavado con el drenaje"),
    "volatilizacion_n_kg_ha_anio": ("kg N/ha/año", "sum(L_vol) / H", "Nitrógeno del fertilizante perdido al aire"),
    "fijacion_n_kg_ha_anio": ("kg N/ha/año", "sum(fijación) / H", "Nitrógeno fijado por leguminosas"),
    "fertilizante_n_kg_ha_anio": ("kg N/ha/año", "sum(fertilizante) / H", "Nitrógeno aplicado"),
    "exportacion_n_kg_ha_anio": ("kg N/ha/año", "sum(N cosechado) / H", "Nitrógeno que sale con la cosecha"),
    "balance_n_mineral_kg_ha": ("kg N/ha", "N(fin) - N(0)", "Cambio del nitrógeno disponible en el suelo"),
    "cambio_carbono_t_ha": ("t C/ha", "C(fin) - C(0)", "Cambio del carbono orgánico del suelo (0-30 cm)"),
    "cambio_carbono_t_ha_anio": ("t C/ha/año", "(C(fin) - C(0)) / H", "Cambio anual del carbono del suelo"),
    "cobertura_media": ("fracción", "media diaria de V", "Qué tanto suelo cubre la vegetación en promedio"),
    "dias_suelo_desnudo_anio": ("días/año", "días con (1 - V)(1 - f_res) > 1 - umbral, / H",
                                "Días con el suelo desprotegido"),
    "lluvia_intensa_sobre_suelo_desnudo_mm_anio": ("mm/año", "sum(P * 1[P >= P_int] * (1 - V)(1 - f_res)) / H",
                                                   "Lluvia intensa que cae sobre suelo desprotegido"),
    "exposicion_erosiva_mm_anio": ("mm/año", "alias de lluvia_intensa_sobre_suelo_desnudo_mm_anio",
                                   "Nombre obsoleto (v1); usar lluvia_intensa_sobre_suelo_desnudo_mm_anio. "
                                   "exposicion_erosiva es la función de Datos (T-D6)"),
    "rendimiento_relativo": ("adimensional", "media por temporada de Y / Y_pot",
                             "Cosecha lograda frente a la posible sin falta de agua ni nitrógeno"),
    "indice_productivo": ("adimensional", "media por temporada de Y / Y_max (Y_max: solo radiación)",
                          "Cosecha lograda frente a la que permitiría el sol del lugar; incluye el efecto del frío "
                          "o el calor"),
    "produccion_relativa_anio": ("temporadas equivalentes/año",
                                 "sum(Y / Y_max en temporadas cosechadas) / H",
                                 "Producción cosechada por año, medida en temporadas de rendimiento pleno (1 = una "
                                 "cosecha al potencial de radiación del lugar); permite comparar cultivos distintos"),
    "costo_anio": ("moneda/ha/año", "(riego * c_riego + N * c_N + semilla + labranzas) / H",
                   "Costo directo estimado con los precios que dio el usuario"),
    "cierre_balance_agua_mm": ("mm", "max |W(t) - W(t-1) - (P + I - ETa - R - D)|",
                               "Error numérico del balance de agua (debe ser ~0)"),
}

OBSOLETOS = {"exposicion_erosiva_mm_anio": "lluvia_intensa_sobre_suelo_desnudo_mm_anio"}

DEFINICIONES_TEMPORADA = {
    "rendimiento_kg_ha": ("kg MS/ha", "IC * B a la cosecha (0 si es cobertura)"),
    "rendimiento_pot_kg_ha": ("kg MS/ha", "IC * B_pot sin estrés hídrico ni de N (B_pot si es cobertura)"),
    "rendimiento_relativo": ("adimensional", "Y / Y_pot"),
    "aptitud_termica": ("adimensional", "Y_pot / Y_max: cuánto deja crecer la temperatura (1 = sin límite)"),
    "biomasa_kg_ha": ("kg MS/ha", "B a la cosecha"),
    "lluvia_mm": ("mm", "sum(P) en la temporada"),
    "riego_mm": ("mm", "sum(I_bruto) en la temporada"),
    "et_real_mm": ("mm", "sum(ETa) en la temporada"),
    "et_cultivo_mm": ("mm", "sum(ETc) en la temporada"),
    "deficit_relativo": ("adimensional", "1 - sum(ETa) / sum(ETc)"),
    "dias_estres": ("días", "días con Ks < 0,99"),
    "absorcion_n_kg_ha": ("kg N/ha", "sum(U) desde el suelo"),
    "fijacion_n_kg_ha": ("kg N/ha", "sum(fijación)"),
    "lixiviacion_n_kg_ha": ("kg N/ha", "sum(L_lix) en la temporada"),
}


def por_miembro(reg: dict, prog: dict, H: int, p_intensa: float, umbral_cobertura: float,
                costos_fijos: np.ndarray | None = None, costos: dict | None = None) -> dict[str, np.ndarray]:
    """Indicadores de horizonte (M,) para cada miembro."""
    cultivo = prog["cult"] >= 0
    etc_c = np.where(cultivo, reg["ETc"], 0).sum(1)
    eta_c = np.where(cultivo, reg["ETa"], 0).sum(1)
    w_prev = np.concatenate([reg["inicial"]["W"][:, None], reg["W"][:, :-1]], axis=1)
    cierre = reg["W"] - w_prev - (reg["P"] + reg["I_neto"] - reg["ETa"] - reg["R"] - reg["D"])
    logrado = np.where(prog["cosechar"], reg["rend"], reg["b_cosecha"])
    rel_t = np.where(prog["cosecha"], logrado / np.maximum(reg["rend_pot"], 1e-9), 0.0)
    prod_t = np.where(prog["cosecha"], logrado / np.maximum(reg["rend_max"], 1e-9), 0.0)
    n_temp = prog["cosecha"].sum(1)
    out = {
        "riego_mm_anio": reg["I_bruto"].sum(1) / H,
        "et_real_mm_anio": reg["ETa"].sum(1) / H,
        "drenaje_mm_anio": reg["D"].sum(1) / H,
        "escorrentia_mm_anio": reg["R"].sum(1) / H,
        "deficit_relativo": np.where(etc_c > 0, 1 - eta_c / np.maximum(etc_c, 1e-9), 0.0),
        "dias_estres_anio": (cultivo & (reg["K"] < 0.99)).sum(1) / H,
        "lixiviacion_n_kg_ha_anio": reg["L_lix"].sum(1) / H,
        "volatilizacion_n_kg_ha_anio": reg["L_vol"].sum(1) / H,
        "fijacion_n_kg_ha_anio": reg["fijacion"].sum(1) / H,
        "fertilizante_n_kg_ha_anio": (reg["fert_suelo"] + reg["L_vol"]).sum(1) / H,
        "exportacion_n_kg_ha_anio": reg["N_export"].sum(1) / H,
        "balance_n_mineral_kg_ha": reg["N"][:, -1] - reg["inicial"]["N"],
        "cambio_carbono_t_ha": reg["C"][:, -1] - reg["inicial"]["C"],
        "cambio_carbono_t_ha_anio": (reg["C"][:, -1] - reg["inicial"]["C"]) / H,
        "cobertura_media": reg["V"].mean(1),
        "dias_suelo_desnudo_anio": (reg["desnudo"] > 1 - umbral_cobertura).sum(1) / H,
        "lluvia_intensa_sobre_suelo_desnudo_mm_anio": (reg["P"] * (reg["P"] >= p_intensa) * reg["desnudo"]).sum(1) / H,
        "rendimiento_relativo": np.where(n_temp > 0, rel_t.sum(1) / np.maximum(n_temp, 1), np.nan),
        "indice_productivo": np.where(n_temp > 0, prod_t.sum(1) / np.maximum(n_temp, 1), np.nan),
        "produccion_relativa_anio": np.where(prog["cosecha"] & prog["cosechar"], prod_t, 0.0).sum(1) / H,
        "cierre_balance_agua_mm": np.abs(cierre).max(1),
    }
    out["exposicion_erosiva_mm_anio"] = out["lluvia_intensa_sobre_suelo_desnudo_mm_anio"]
    if costos is not None and costos_fijos is not None:
        out["costo_anio"] = (reg["I_bruto"].sum(1) * float(costos.get("riego_por_mm", 0.0)) + costos_fijos) / H
    return out


def costos_fijos_estrategia(estrategia, costos: dict) -> float:
    """Costos que no dependen del clima: semilla, fertilizante y labranza de todas las temporadas."""
    total = 0.0
    semilla = costos.get("semilla", {})
    for t in estrategia.temporadas:
        if t.cultivo not in semilla:
            raise KeyError(f"costo de semilla de {t.cultivo} no dado; sin él el costo queda PENDIENTE")
        total += float(semilla[t.cultivo])
        total += sum(f.kg_n for f in t.fertilizacion) * float(costos.get("n_por_kg", 0.0))
        total += float(costos.get("labranza", 0.0)) * (t.labranza_siembra + (t.residuos == "incorporar"))
    return total


def por_temporada(reg: dict, prog: dict, n_temporadas: int) -> dict[str, np.ndarray]:
    """Indicadores (M, n_temporadas) de cada temporada de la estrategia."""
    M = reg["P"].shape[0]
    out = {k: np.full((M, n_temporadas), np.nan) for k in DEFINICIONES_TEMPORADA}
    for k in range(n_temporadas):
        mk = prog["temporada"] == k
        fin = mk & prog["cosecha"]

        def s(key):
            return np.where(mk, reg[key], 0).sum(1)
        out["rendimiento_kg_ha"][:, k] = np.where(fin, reg["rend"], 0).sum(1)
        out["rendimiento_pot_kg_ha"][:, k] = np.where(fin, reg["rend_pot"], 0).sum(1)
        out["biomasa_kg_ha"][:, k] = np.where(fin, reg["b_cosecha"], 0).sum(1)
        exporta = np.where(fin, prog["cosechar"], False).any(1)
        logrado = np.where(exporta, out["rendimiento_kg_ha"][:, k], out["biomasa_kg_ha"][:, k])
        out["rendimiento_relativo"][:, k] = logrado / np.maximum(out["rendimiento_pot_kg_ha"][:, k], 1e-9)
        out["aptitud_termica"][:, k] = out["rendimiento_pot_kg_ha"][:, k] / np.maximum(
            np.where(fin, reg["rend_max"], 0).sum(1), 1e-9)
        out["lluvia_mm"][:, k] = s("P")
        out["riego_mm"][:, k] = s("I_bruto")
        out["et_real_mm"][:, k] = s("ETa")
        out["et_cultivo_mm"][:, k] = s("ETc")
        out["deficit_relativo"][:, k] = 1 - s("ETa") / np.maximum(s("ETc"), 1e-9)
        out["dias_estres"][:, k] = (mk & (reg["K"] < 0.99)).sum(1)
        out["absorcion_n_kg_ha"][:, k] = s("U")
        out["fijacion_n_kg_ha"][:, k] = s("fijacion")
        out["lixiviacion_n_kg_ha"][:, k] = s("L_lix")
    return out


def mensual(reg: dict, H: int) -> dict[str, np.ndarray]:
    """Trayectorias mensuales (M, 12 H): estados como media del mes y flujos como suma del mes."""
    mes = (np.arange(H)[:, None] * 12 + MES_DE_DIA[None, :]).reshape(-1)
    n_mes = 12 * H
    cuenta = np.bincount(mes, minlength=n_mes)
    out = {}
    for k in ("W", "agua_raiz", "N", "C", "B", "V", "desnudo"):
        out[k] = np.stack([np.bincount(mes, weights=fila, minlength=n_mes) for fila in reg[k]]) / cuenta
    for k in ("P", "ETa", "I_bruto", "D", "R", "L_lix"):
        out[k] = np.stack([np.bincount(mes, weights=fila, minlength=n_mes) for fila in reg[k]])
    return out
