# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Núcleo del gemelo digital AGROVERSE: dx/dt = f(x, u, e, theta) con x = [W, N, C, B, V] a paso diario.

Uso como biblioteca:
    from gemelo import simular, optimizar_rotacion
    doc = simular("ejemplos/escenario_ames.yaml")      # dict con el contrato contratos/gemelo_api.md
Uso por consola: python -m gemelo --help
"""
from gemelo.simulador import VERSION_MODELO

__version__ = VERSION_MODELO
__all__ = ["simular", "optimizar_rotacion", "definiciones", "__version__"]


def __getattr__(nombre):
    if nombre in ("simular", "optimizar_rotacion", "definiciones"):
        from gemelo import api
        return getattr(api, nombre)
    raise AttributeError(nombre)
