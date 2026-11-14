# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Catálogo de cultivos con procedencia: lee el formato de fao56.yaml (rama datos) y los parámetros propios del gemelo."""
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from gemelo.procedencia import REFERENCIAS, Parametro, ParametroPendiente

_NUM = re.compile(r"\d+(?:,\d+)?")
_ETAPAS = re.compile(r"(\d+)\s*/\s*(\d+)(?:\s*-\s*\d+)?\s*/\s*(\d+)\s*/\s*(\d+)")

# Parámetros de biomasa y nitrógeno que todo cultivo simulable debe tener
CLAVES_BIOLOGICAS = ("rue", "t_base", "t_opt", "t_max", "indice_cosecha", "n_biomasa", "indice_cosecha_n", "ndfa")


def _a_float(s: str) -> float:
    return float(s.replace(",", "."))


def leer_kc(texto) -> tuple[float, tuple[float, float]] | None:
    """Texto de Kc de FAO-56 -> (central, (min, max)).

    "0,60–0,35" es un rango: central = media. "0,4 helado; 0,7 no helado" son alternativas: central = la primera.
    """
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        return float(texto), (float(texto), float(texto))
    nums = [_a_float(n) for n in _NUM.findall(str(texto))]
    if not nums:
        return None
    rango = (min(nums), max(nums))
    if "–" in str(texto) and len(nums) >= 2 and ";" not in str(texto):
        return (nums[0] + nums[1]) / 2, rango
    return nums[0], rango


def leer_etapas(texto, variante: str | None = None) -> tuple[int, int, int, int] | None:
    """Etapas ini/des/med/fin en días ("20/30-35/60/25" toma 30). None si no hay etapas.

    Sin `variante` toma la primera; con `variante` toma la que contiene ese texto (p. ej. "centro EE. UU.").
    """
    if texto is None:
        return None
    partes = str(texto).split(";")
    if variante is not None:
        partes = [p for p in partes if variante.lower() in p.lower()]
        if not partes:
            raise ValueError(f"variante de etapas {variante!r} no está en {texto!r}")
    m = _ETAPAS.search(partes[0])
    return tuple(int(g) for g in m.groups()) if m else None


@dataclass
class Cultivo:
    id: str
    nombre: str
    especie: str
    familia: str
    funcion: list[str]
    apto_rotacion: bool
    parametros: dict[str, Parametro] = field(default_factory=dict)
    etapas: tuple[int, int, int, int] | None = None
    etapas_referencia: str = ""
    motivo_no_apto: str = ""

    @property
    def fija_n(self) -> bool:
        return "fijadora_n" in self.funcion

    def p(self, clave) -> Parametro:
        return self.parametros[clave]

    def pendientes(self, etapas_usuario=None) -> list[str]:
        faltan = [k for k, v in self.parametros.items() if not v.disponible]
        faltan += [k for k in CLAVES_BIOLOGICAS if k not in self.parametros]
        if self.etapas is None and etapas_usuario is None:
            faltan.append("etapas")
        return sorted(set(faltan))

    def verificar_simulable(self, etapas_usuario=None):
        if not self.apto_rotacion:
            raise ParametroPendiente(f"{self.nombre}: no apto para rotación anual ({self.motivo_no_apto})")
        faltan = self.pendientes(etapas_usuario)
        if faltan:
            raise ParametroPendiente(f"{self.nombre}: parámetros PENDIENTE {faltan}")

    def a_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "especie": self.especie, "familia": self.familia,
                "funcion": self.funcion, "apto_rotacion": self.apto_rotacion, "fija_n": self.fija_n,
                "etapas_dias": list(self.etapas) if self.etapas else None, "etapas_referencia": self.etapas_referencia,
                "pendientes": self.pendientes(), "parametros": {k: v.a_dict() for k, v in self.parametros.items()}}


def _parametro_fao(nombre, texto, ficha, ref) -> Parametro:
    leido = leer_kc(texto)
    if leido is None:
        return Parametro(nombre, None, "adimensional", "PENDIENTE", referencia=f"{ref}: sin valor")
    v, r = leido
    return Parametro(nombre, v, "adimensional", "FUENTE", referencia=f"{ref}: '{texto}'", ficha=ficha,
                     rango=r if r[0] < r[1] else None)


def construir_cultivo(cid: str, d: dict, comunes: dict) -> Cultivo:
    fao = d["fao56"]
    ficha = fao.get("fuente_id")
    ref = "FAO-56 Tablas 12 y 22 vía INV-ROT §3"
    ps: dict[str, Parametro] = {}
    for k in ("kc_ini", "kc_mid", "kc_end"):
        ps[k] = _parametro_fao(k, fao.get(k), ficha, ref)
    if fao.get("zr_min") is not None and fao.get("zr_max") is not None:
        lo, hi = float(fao["zr_min"]), float(fao["zr_max"])
        ps["zr_max"] = Parametro("zr_max", (lo + hi) / 2, "m", "FUENTE", referencia=f"{ref}: Zr {lo}-{hi} m",
                                 ficha=ficha, rango=(lo, hi))
    else:
        ps["zr_max"] = Parametro("zr_max", None, "m", "PENDIENTE", referencia=ref)
    ps["p"] = (Parametro("p", float(fao["p"]), "adimensional", "FUENTE", referencia=f"{ref}: p", ficha=ficha)
               if fao.get("p") is not None else Parametro("p", None, "adimensional", "PENDIENTE"))
    if fao.get("agua_min") is not None:
        ps["agua_temporada"] = Parametro("agua_temporada", (fao["agua_min"] + fao["agua_max"]) / 2, "mm",
                                         "FUENTE", referencia="FAO-56 vía INV-ROT §3: necesidad de agua de la temporada",
                                         ficha=fao.get("fuente_agua"), rango=(fao["agua_min"], fao["agua_max"]))
    if d.get("altura_m") is not None:
        ps["altura_m"] = Parametro("altura_m", float(d["altura_m"]), "m", "FUENTE",
                                   referencia="FAO-56 Tabla 12: altura máxima", ficha="EV-ROT-010")
    for k in CLAVES_BIOLOGICAS:
        if k in d:
            v, lo, hi = (float(x) for x in d[k])
            meta = comunes[k]
            ps[k] = Parametro(k, v, meta["unidad"], meta["etiqueta"], referencia=meta["referencia"],
                              rango=(lo, hi) if lo < hi else None)
    return Cultivo(id=cid, nombre=d["nombre"], especie=d.get("especie", ""), familia=d.get("familia", ""),
                   funcion=list(d.get("funcion", [])), apto_rotacion=bool(d.get("apto_rotacion", True)),
                   parametros=ps, etapas=leer_etapas(fao.get("etapas")), etapas_referencia=str(fao.get("etapas")),
                   motivo_no_apto=d.get("motivo_no_apto", ""))


@lru_cache(maxsize=4)
def _leer_catalogo(ruta: str) -> dict:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


def cargar_catalogo(ruta: str | Path | None = None) -> dict[str, Cultivo]:
    datos = _leer_catalogo(str(ruta or REFERENCIAS / "cultivos.yaml"))
    return {cid: construir_cultivo(cid, d, datos["comunes"]) for cid, d in datos["cultivos"].items()}
