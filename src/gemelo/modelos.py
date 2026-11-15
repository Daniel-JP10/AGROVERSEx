# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Estructuras de datos del gemelo: Finca, Lote, decisiones de manejo u(t), Estrategia y estado del gemelo.

Fechas nominales: "A1-03-15" = año 1 del horizonte, 15 de marzo (calendario de 365 días, ver clima.py).
"""
import re
from dataclasses import dataclass, field

from gemelo.clima import INICIO_MES, DIAS_MES
from gemelo.procedencia import NATURALEZAS

_FECHA = re.compile(r"^A(\d+)-(\d{2})-(\d{2})$")
_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def dia_nominal(fecha: str) -> int:
    """'A1-03-15' -> índice de día desde el inicio del horizonte (0 = 1 de enero del año 1)."""
    m = _FECHA.match(fecha.strip())
    if not m:
        raise ValueError(f"fecha nominal {fecha!r}: se espera A<año>-MM-DD, p. ej. A1-03-15")
    anio, mes, dia = (int(g) for g in m.groups())
    if anio < 1 or not 1 <= mes <= 12 or not 1 <= dia <= DIAS_MES[mes - 1]:
        raise ValueError(f"fecha nominal {fecha!r} fuera de rango (sin 29 de febrero)")
    return 365 * (anio - 1) + int(INICIO_MES[mes - 1]) + dia - 1


def fecha_nominal(dia: int) -> str:
    anio, doy = divmod(int(dia), 365)
    mes = int((INICIO_MES <= doy).sum()) - 1
    return f"A{anio + 1}-{mes + 1:02d}-{doy - INICIO_MES[mes] + 1:02d}"


def fecha_legible(dia: int) -> str:
    anio, doy = divmod(int(dia), 365)
    mes = int((INICIO_MES <= doy).sum()) - 1
    return f"{doy - INICIO_MES[mes] + 1} {_MESES[mes]} año {anio + 1}"


@dataclass
class Finca:
    id: str
    nombre: str
    lotes: list[str] = field(default_factory=list)


@dataclass
class Lote:
    id: str
    nombre: str
    lat: float
    lon: float
    unidad_id: str | None = None
    finca_id: str | None = None
    geometria_wkt: str | None = None
    area_ha: float | None = None
    zona_demo: str | None = None


@dataclass
class Riego:
    """Riego automático (FAO-56 cap. 8): se repone a capacidad de campo cuando el agotamiento supera umbral * RAW."""
    modo: str = "ninguno"           # ninguno | automatico
    umbral: float = 1.0             # fracción de RAW que dispara el riego
    tope_mm: float | None = None    # lámina bruta máxima en la temporada

    def __post_init__(self):
        if self.modo not in ("ninguno", "automatico"):
            raise ValueError(f"modo de riego {self.modo!r}")
        if self.umbral <= 0:
            raise ValueError("umbral de riego debe ser > 0")


@dataclass
class Fertilizacion:
    dia: int          # días después de la siembra
    kg_n: float       # kg N/ha aplicados

    def __post_init__(self):
        if self.kg_n < 0 or self.dia < 0:
            raise ValueError("fertilización negativa")


@dataclass
class Temporada:
    """Un ciclo de cultivo dentro de una rotación: es la unidad de decisión u(t)."""
    cultivo: str
    siembra: int                                   # día nominal
    etapas: tuple[int, int, int, int] | None = None
    etapas_variante: str | None = None
    riego: Riego = field(default_factory=Riego)
    fertilizacion: list[Fertilizacion] = field(default_factory=list)
    cosechar: bool = True                          # False: cultivo de cobertura que se incorpora entero
    residuos: str = "superficie"                   # superficie | incorporar
    labranza_siembra: bool = False                 # labranza al sembrar: incorpora el residuo superficial

    def __post_init__(self):
        if self.residuos not in ("superficie", "incorporar"):
            raise ValueError(f"residuos {self.residuos!r}")
        if self.siembra < 0:
            raise ValueError("siembra antes del inicio del horizonte")

    def a_dict(self, duracion: int | None = None) -> dict:
        d = {"cultivo": self.cultivo, "siembra": fecha_nominal(self.siembra),
             "siembra_legible": fecha_legible(self.siembra),
             "etapas_dias": list(self.etapas) if self.etapas else None, "etapas_variante": self.etapas_variante,
             "riego": {"modo": self.riego.modo, "umbral": self.riego.umbral, "tope_mm": self.riego.tope_mm},
             "fertilizacion": [{"dia": f.dia, "kg_n": f.kg_n} for f in self.fertilizacion],
             "cosechar": self.cosechar, "residuos": self.residuos, "labranza_siembra": self.labranza_siembra}
        if duracion is not None:
            d["cosecha"] = fecha_nominal(self.siembra + duracion - 1)
            d["cosecha_legible"] = fecha_legible(self.siembra + duracion - 1)
        return d


@dataclass
class Estrategia:
    """Secuencia de temporadas (rotación) que el gemelo simula y compara."""
    id: str
    nombre: str
    temporadas: list[Temporada]
    descripcion: str = ""
    etiqueta: str = "ilustrativa"     # p. ej. "FUENTE EV-ROT-022 (rotación habitual)" o "candidata NSGA-II"

    def secuencia(self) -> str:
        return " -> ".join(t.cultivo for t in self.temporadas)


@dataclass
class EstadoGemelo:
    """Instantánea del estado x(t) = [W, N, C, B, V] con su naturaleza (simulado salvo calibración)."""
    dia: int
    agua_mm: float
    n_mineral_kg_ha: float
    carbono_t_ha: float
    biomasa_kg_ha: float
    cobertura: float
    naturaleza: str = "simulado"

    def __post_init__(self):
        if self.naturaleza not in NATURALEZAS:
            raise ValueError(self.naturaleza)

    def vector(self) -> list[float]:
        return [self.agua_mm, self.n_mineral_kg_ha, self.carbono_t_ha, self.biomasa_kg_ha, self.cobertura]
