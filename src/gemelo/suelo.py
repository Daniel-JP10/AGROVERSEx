# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Caracterización del suelo: SoilGrids 2.0 -> textura, COS, N -> propiedades hidráulicas (Saxton y Rawls, 2006).

Unidades: fracciones de arena y arcilla en kg/kg; MO en % en peso; contenidos de agua en m³/m³; Ksat en mm/h.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from gemelo.procedencia import REFERENCIAS, Parametro, cargar_tabla

SAXTON_RAWLS = "Saxton y Rawls (2006), Soil Sci. Soc. Am. J. 70: 1569-1578, Tabla 1"
DOMINIO_SR = {"mo_pct_max": 8.0, "arcilla_max": 0.60}
_REF_AS = yaml.safe_load((REFERENCIAS / "agua_suelo.yaml").read_text(encoding="utf-8"))


def saxton_rawls(arena, arcilla, mo_pct) -> dict:
    """Ecuaciones de la Tabla 1 de Saxton y Rawls (2006). Acepta escalares o arreglos.

    Devuelve theta_pmp (1500 kPa), theta_cc (33 kPa), theta_sat, ksat_mm_h y la marca fuera_dominio.
    Fuera del dominio de calibración (MO > 8 %, arcilla > 60 %) se recortan las entradas y se marca.
    """
    S = np.asarray(arena, float)
    C0 = np.asarray(arcilla, float)
    OM0 = np.asarray(mo_pct, float)
    fuera = (OM0 > DOMINIO_SR["mo_pct_max"]) | (C0 > DOMINIO_SR["arcilla_max"])
    C = np.minimum(C0, DOMINIO_SR["arcilla_max"])
    OM = np.minimum(OM0, DOMINIO_SR["mo_pct_max"])
    t1500t = -0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * S * OM - 0.013 * C * OM + 0.068 * S * C + 0.031
    t1500 = t1500t + (0.14 * t1500t - 0.02)
    t33t = -0.251 * S + 0.195 * C + 0.011 * OM + 0.006 * S * OM - 0.027 * C * OM + 0.452 * S * C + 0.299
    t33 = t33t + (1.283 * t33t ** 2 - 0.374 * t33t - 0.015)
    ts33t = 0.278 * S + 0.034 * C + 0.022 * OM - 0.018 * S * OM - 0.027 * C * OM - 0.584 * S * C + 0.078
    ts33 = ts33t + (0.636 * ts33t - 0.107)
    tsat = t33 + ts33 - 0.097 * S + 0.043
    B = (np.log(1500.0) - np.log(33.0)) / (np.log(t33) - np.log(t1500))
    lam = 1.0 / B
    ksat = 1930.0 * np.maximum(tsat - t33, 0.0) ** (3.0 - lam)
    return {"theta_pmp": t1500, "theta_cc": t33, "theta_sat": tsat, "ksat_mm_h": ksat, "fuera_dominio": fuera}


def grupo_hidrologico(ksat_mm_h: float) -> str:
    """Grupo A-D por Ksat (NRCS NEH 630 cap. 7, profundidad a capa impermeable > 100 cm)."""
    u = _REF_AS["grupo_hidrologico"]["umbrales_um_s"]
    k = ksat_mm_h / 3.6  # mm/h -> µm/s
    return "A" if k > u["A"] else "B" if k > u["B"] else "C" if k > u["C"] else "D"


def numeros_curva(grupo: str) -> dict[str, float]:
    t = _REF_AS["numero_curva"]
    return {"cultivo": float(t["cultivo_en_hilera"][grupo]), "desnudo": float(t["barbecho_desnudo"][grupo]),
            "residuo": float(t["barbecho_con_residuo"][grupo])}


def coef_drenaje(ksat_mm_h, a=0.0866, b=0.35):
    """tau de AquaCrop: fracción diaria del exceso sobre capacidad de campo que drena (0-1)."""
    return np.clip(a * (np.asarray(ksat_mm_h, float) * 24.0) ** b, 0.0, 1.0)


def numero_curva_efectivo(cn: dict, cobertura_viva, cobertura_residuo):
    """Interpola el CN de TR-55 según la cobertura (INFERENCIA: TR-55 da clases discretas, no una función)."""
    v = np.clip(cobertura_viva, 0, 1)
    r = np.clip(cobertura_residuo, 0, 1)
    suelo = cn["desnudo"] * (1 - r) + cn["residuo"] * r
    return cn["cultivo"] * v + suelo * (1 - v)


def escorrentia_scs(precip, cn):
    """Escorrentía diaria por número de curva: S = 25400/CN - 254, Ia = 0,2 S (mm)."""
    p = np.asarray(precip, float)
    s = 25400.0 / np.asarray(cn, float) - 254.0
    ia = 0.2 * s
    return np.where(p > ia, (p - ia) ** 2 / np.maximum(p - ia + s, 1e-12), 0.0)


# --------------------------------------------------------------------------------------------- perfil de suelo

@dataclass
class PerfilSuelo:
    """Propiedades del perfil del lote. Cada valor es un Parametro con procedencia."""
    parametros: dict[str, Parametro] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    fuente: str = ""

    def __getitem__(self, k) -> Parametro:
        return self.parametros[k]

    def valor(self, k) -> float:
        return self.parametros[k].exigir()

    def calibrar(self, **valores) -> "PerfilSuelo":
        """Datos locales. La textura recalcula la hidráulica; las mediciones hidráulicas directas se aplican después."""
        valores = {k: v for k, v in valores.items() if v is not None}
        nuevos = dict(self.parametros)
        if "cn_suelo" in valores and "cn_suelo" not in nuevos:
            nuevos["cn_suelo"] = Parametro("cn_suelo", float(valores["cn_suelo"]), "kg C/kg N", "FUENTE")
        desconocidas = [k for k in valores if k not in nuevos]
        if desconocidas:
            raise KeyError(f"calibración de suelo: propiedades desconocidas {desconocidas}")
        textura = {k: v for k, v in valores.items() if k in ("arena", "arcilla", "mo_pct")}
        for k, v in textura.items():
            nuevos[k] = nuevos[k].calibrar(v)
        perfil = PerfilSuelo(nuevos, list(self.avisos), self.fuente)
        if textura:
            perfil = completar_hidraulica(perfil, recalcular=True)
        for k, v in valores.items():
            if k not in textura:
                perfil.parametros[k] = perfil.parametros[k].calibrar(v)
        return perfil

    def a_dict(self) -> dict:
        return {"fuente": self.fuente, "avisos": self.avisos,
                "parametros": {k: v.a_dict() for k, v in self.parametros.items()}}


_DFACTOR = {"bdod": 100.0, "clay": 10.0, "sand": 10.0, "silt": 10.0, "soc": 10.0, "nitrogen": 100.0, "phh2o": 10.0}
_ESPESOR = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15, "30-60cm": 30, "60-100cm": 40, "100-200cm": 100}


def _media_ponderada(capas: dict, prop: str, estad: str, hasta_cm: int) -> float | None:
    tot, peso = 0.0, 0.0
    for etiqueta, esp in _ESPESOR.items():
        sup = int(etiqueta.split("-")[0])
        if sup >= hasta_cm or etiqueta not in capas.get(prop, {}):
            continue
        v = capas[prop][etiqueta].get(estad)
        if v is None:
            continue
        e = min(esp, hasta_cm - sup)
        tot += v / _DFACTOR[prop] * e
        peso += e
    return tot / peso if peso else None


def _stock_cos(capas: dict, estad: str, hasta_cm: int) -> float | None:
    """COS 0-hasta_cm en t C/ha = sum(SOC g/kg * BD kg/dm³ * espesor cm * 0,1). Sin fragmentos gruesos."""
    tot = 0.0
    for etiqueta, esp in _ESPESOR.items():
        sup = int(etiqueta.split("-")[0])
        if sup >= hasta_cm:
            continue
        try:
            soc = capas["soc"][etiqueta][estad] / _DFACTOR["soc"]
            bd = capas["bdod"][etiqueta][estad] / _DFACTOR["bdod"]
        except (KeyError, TypeError):
            return None
        tot += soc * bd * min(esp, hasta_cm - sup) * 0.1
    return tot


def leer_soilgrids(ruta: str | Path) -> dict:
    """Respuesta JSON de la API REST de SoilGrids 2.0 -> {prop: {capa: {mean, Q0.05, Q0.95}}}."""
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    capas = {}
    for capa in d["properties"]["layers"]:
        capas[capa["name"]] = {x["label"]: x["values"] for x in capa["depths"]}
    lon, lat = d.get("geometry", {}).get("coordinates", [None, None])
    return {"capas": capas, "lat": lat, "lon": lon}


def perfil_desde_soilgrids(ruta: str | Path, profundidad_m: float | None = None) -> PerfilSuelo:
    sg = leer_soilgrids(ruta)
    capas = sg["capas"]
    tabla = cargar_tabla("agua_suelo.yaml")
    prof = tabla["profundidad_perfil_m"] if profundidad_m is None else Parametro(
        "profundidad_perfil_m", float(profundidad_m), "m", "FUENTE", referencia="dato del usuario", naturaleza="observado")
    hasta = int(round(prof.exigir() * 100))
    ref = f"SoilGrids 2.0 (ISRIC), media 0-{hasta} cm ponderada por espesor; rango Q0.05-Q0.95; CC BY 4.0"
    ps: dict[str, Parametro] = {"profundidad_perfil_m": prof}
    for prop, nombre, unidad, factor in (("sand", "arena", "kg/kg", 0.01), ("clay", "arcilla", "kg/kg", 0.01),
                                         ("bdod", "densidad_aparente", "kg/dm³", 1.0), ("phh2o", "ph", "-", 1.0)):
        m = _media_ponderada(capas, prop, "mean", hasta)
        lo = _media_ponderada(capas, prop, "Q0.05", hasta)
        hi = _media_ponderada(capas, prop, "Q0.95", hasta)
        if m is None:
            ps[nombre] = Parametro(nombre, None, unidad, "PENDIENTE", referencia="SoilGrids sin dato")
            continue
        ps[nombre] = Parametro(nombre, m * factor, unidad, "FUENTE", referencia=ref, ficha=None,
                               rango=(min(lo, m) * factor, max(hi, m) * factor) if lo is not None else None,
                               distribucion="triangular", naturaleza="estimado")
    soc = _media_ponderada(capas, "soc", "mean", hasta)
    fc = tabla.valor("fraccion_carbono_mo")
    if soc is not None:
        mo = soc / 10.0 / fc  # g/kg -> % y COS -> MO
        lo, hi = (_media_ponderada(capas, "soc", q, hasta) for q in ("Q0.05", "Q0.95"))
        ps["mo_pct"] = Parametro("mo_pct", mo, "%", "INFERENCIA", referencia=f"{ref}; MO = COS/0,58",
                                 rango=(min(lo / 10 / fc, mo), max(hi / 10 / fc, mo)), distribucion="triangular")
    cn_t = cargar_tabla("carbono_nitrogeno.yaml")
    h_cos = int(cn_t.valor("profundidad_cos_cm"))
    stock = _stock_cos(capas, "mean", h_cos)
    if stock is not None:
        lo, hi = _stock_cos(capas, "Q0.05", h_cos), _stock_cos(capas, "Q0.95", h_cos)
        ps["cos_t_ha"] = Parametro("cos_t_ha", stock, "t C/ha", "FUENTE",
                                   referencia=f"SoilGrids 2.0: COS 0-{h_cos} cm = sum(SOC * BD * espesor); sin fragmentos gruesos",
                                   rango=(min(lo, stock), max(hi, stock)), distribucion="triangular")
    soc30 = _media_ponderada(capas, "soc", "mean", h_cos)
    n30 = _media_ponderada(capas, "nitrogen", "mean", h_cos)
    if soc30 and n30:
        ps["cn_suelo"] = Parametro("cn_suelo", soc30 / n30, "kg C/kg N", "FUENTE",
                                   referencia=f"SoilGrids 2.0: soc/nitrogen 0-{h_cos} cm")
    perfil = PerfilSuelo(ps, [], f"SoilGrids 2.0 punto ({sg['lat']}, {sg['lon']})")
    return completar_hidraulica(perfil)


def perfil_manual(arena: float, arcilla: float, mo_pct: float, cos_t_ha: float, cn_suelo: float | None = None,
                  profundidad_m: float = 1.0, referencia: str = "dato del usuario") -> PerfilSuelo:
    def obs(n, v, u):
        return Parametro(n, float(v), u, "FUENTE", referencia=referencia, naturaleza="observado")
    ps = {"profundidad_perfil_m": obs("profundidad_perfil_m", profundidad_m, "m"), "arena": obs("arena", arena, "kg/kg"),
          "arcilla": obs("arcilla", arcilla, "kg/kg"), "mo_pct": obs("mo_pct", mo_pct, "%"),
          "cos_t_ha": obs("cos_t_ha", cos_t_ha, "t C/ha")}
    if cn_suelo is not None:
        ps["cn_suelo"] = obs("cn_suelo", cn_suelo, "kg C/kg N")
    return completar_hidraulica(PerfilSuelo(ps, [], referencia))


def completar_hidraulica(perfil: PerfilSuelo, recalcular: bool = False) -> PerfilSuelo:
    """Añade theta_cc, theta_pmp, theta_sat, ksat, grupo hidrológico y tau con su incertidumbre."""
    ps = dict(perfil.parametros)
    avisos = [a for a in perfil.avisos if "Saxton" not in a] if recalcular else list(perfil.avisos)
    a, c, mo = (ps[k].exigir() for k in ("arena", "arcilla", "mo_pct"))
    r = saxton_rawls(a, c, mo)
    # Rango de ensamble del orden del error estándar que reporta Saxton y Rawls (2006) para cada ecuación
    se = {"theta_pmp": 0.02, "theta_cc": 0.05, "theta_sat": 0.05}
    for k, nombre in (("theta_pmp", "theta_pmp"), ("theta_cc", "theta_cc"), ("theta_sat", "theta_sat")):
        v = float(r[k])
        ps[nombre] = Parametro(nombre, v, "m³/m³", "INFERENCIA",
                               referencia=f"{SAXTON_RAWLS}; entradas de {perfil.fuente or 'usuario'}",
                               rango=(max(v - se[k], 0.01), v + se[k]))
    ks = float(r["ksat_mm_h"])
    ps["ksat_mm_h"] = Parametro("ksat_mm_h", ks, "mm/h", "INFERENCIA", referencia=SAXTON_RAWLS,
                                rango=(ks / 3, ks * 3), contexto="Ksat estimado: incertidumbre de un orden de magnitud")
    if bool(np.any(r["fuera_dominio"])):
        excede = ([f"MO {mo:.1f} % > {DOMINIO_SR['mo_pct_max']} %"] if mo > DOMINIO_SR["mo_pct_max"] else []) + \
                 ([f"arcilla {c:.2f} > {DOMINIO_SR['arcilla_max']}"] if c > DOMINIO_SR["arcilla_max"] else [])
        avisos.append(f"Saxton y Rawls fuera de dominio ({', '.join(excede)}); entradas recortadas al límite. "
                      "Los suelos con mucha materia orgánica o volcánicos (Andisoles) suelen retener más agua de "
                      "la estimada: medir capacidad de campo en laboratorio.")
    grupo = grupo_hidrologico(ks)
    ps["grupo_hidrologico"] = Parametro("grupo_hidrologico", "ABCD".index(grupo), "índice 0=A..3=D", "INFERENCIA",
                                        referencia="NRCS NEH 630 cap. 7 a partir de Ksat estimado",
                                        contexto=f"grupo {grupo}")
    if ps["theta_cc"].valor <= ps["theta_pmp"].valor or ps["theta_sat"].valor <= ps["theta_cc"].valor:
        raise ValueError(f"propiedades hidráulicas incoherentes: {r}")
    return PerfilSuelo(ps, avisos, perfil.fuente)
