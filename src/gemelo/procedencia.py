# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Parámetros con procedencia. Ningún número entra al modelo sin unidad, etiqueta y referencia.

Etiquetas (mismo vocabulario que la rama datos):
- FUENTE: transcrito de una referencia citada. `ficha` es el id EV-* si existe; None = ficha EV pendiente.
- INFERENCIA: derivado de una fuente pero aplicado fuera de su contexto original.
- SUPUESTO: valor de diseño sin referencia directa; siempre lleva rango para el ensamble.
- PENDIENTE: no hay valor defendible. El cálculo que lo necesite se detiene con ParametroPendiente.
"""
from dataclasses import dataclass, field, replace
from pathlib import Path

import yaml

ETIQUETAS = ("FUENTE", "INFERENCIA", "SUPUESTO", "PENDIENTE")
NATURALEZAS = ("observado", "derivado", "estimado", "simulado")
DISTRIBUCIONES = ("uniforme", "triangular")


class ParametroPendiente(ValueError):
    """Se pidió un valor marcado PENDIENTE: falta información para calcular."""


@dataclass(frozen=True)
class Parametro:
    nombre: str
    valor: float | None
    unidad: str
    etiqueta: str
    referencia: str = ""
    ficha: str | None = None
    rango: tuple[float, float] | None = None
    distribucion: str = "uniforme"
    contexto: str = ""
    naturaleza: str = "estimado"

    def __post_init__(self):
        if self.etiqueta not in ETIQUETAS:
            raise ValueError(f"{self.nombre}: etiqueta {self.etiqueta!r} fuera de {ETIQUETAS}")
        if self.valor is None and self.etiqueta != "PENDIENTE":
            raise ValueError(f"{self.nombre}: valor nulo solo se admite con etiqueta PENDIENTE")
        if self.distribucion not in DISTRIBUCIONES:
            raise ValueError(f"{self.nombre}: distribución {self.distribucion!r}")
        if self.naturaleza not in NATURALEZAS:
            raise ValueError(f"{self.nombre}: naturaleza {self.naturaleza!r}")
        if self.rango is not None:
            lo, hi = map(float, self.rango)
            if lo > hi:
                raise ValueError(f"{self.nombre}: rango invertido {self.rango}")
            object.__setattr__(self, "rango", (lo, hi))
            if self.valor is not None and not lo <= self.valor <= hi:
                raise ValueError(f"{self.nombre}: valor {self.valor} fuera del rango {self.rango}")

    @property
    def disponible(self) -> bool:
        return self.valor is not None

    def exigir(self) -> float:
        if self.valor is None:
            raise ParametroPendiente(f"{self.nombre} está PENDIENTE ({self.referencia or 'sin fuente'})")
        return float(self.valor)

    def limites(self) -> tuple[float, float]:
        v = self.exigir()
        return self.rango if self.rango is not None else (v, v)

    def calibrar(self, valor: float, referencia: str = "dato local del usuario", naturaleza: str = "observado"):
        """El agricultor o técnico reemplaza el prior por un dato local: el rango colapsa al valor."""
        return replace(self, valor=float(valor), etiqueta="FUENTE", referencia=referencia, ficha=None,
                       rango=None, naturaleza=naturaleza, contexto=f"calibrado; antes: {self.valor} ({self.etiqueta})")

    def a_dict(self) -> dict:
        return {"nombre": self.nombre, "valor": self.valor, "unidad": self.unidad, "etiqueta": self.etiqueta,
                "referencia": self.referencia, "ficha": self.ficha,
                "rango": list(self.rango) if self.rango else None, "distribucion": self.distribucion,
                "contexto": self.contexto, "naturaleza": self.naturaleza}


def parametro_desde_dict(nombre: str, d: dict) -> Parametro:
    return Parametro(nombre=nombre, valor=None if d.get("valor") is None else float(d["valor"]),
                     unidad=d.get("unidad", "adimensional"), etiqueta=d["etiqueta"],
                     referencia=d.get("referencia", ""), ficha=d.get("ficha"),
                     rango=tuple(d["rango"]) if d.get("rango") else None,
                     distribucion=d.get("distribucion", "uniforme"), contexto=d.get("contexto", ""),
                     naturaleza=d.get("naturaleza", "estimado"))


@dataclass
class TablaParametros:
    """Conjunto nombrado de parámetros (theta de un submodelo) cargado de un YAML de referencias."""
    parametros: dict[str, Parametro] = field(default_factory=dict)

    def __getitem__(self, k) -> Parametro:
        return self.parametros[k]

    def __contains__(self, k) -> bool:
        return k in self.parametros

    def valor(self, k) -> float:
        return self.parametros[k].exigir()

    def items(self):
        return self.parametros.items()

    def con(self, **valores) -> "TablaParametros":
        nuevos = dict(self.parametros)
        for k, v in valores.items():
            nuevos[k] = v if isinstance(v, Parametro) else self.parametros[k].calibrar(v)
        return TablaParametros(nuevos)

    def a_lista(self) -> list[dict]:
        return [p.a_dict() for p in self.parametros.values()]


REFERENCIAS = Path(__file__).resolve().parent / "referencias"


def cargar_tabla(archivo: str) -> TablaParametros:
    datos = yaml.safe_load((REFERENCIAS / archivo).read_text(encoding="utf-8"))
    return TablaParametros({k: parametro_desde_dict(k, v) for k, v in datos["parametros"].items()})
