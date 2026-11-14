# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
from pathlib import Path

import numpy as np
import pytest

from gemelo.clima import ClimaDiario, cargar_power
from gemelo.modelos import Estrategia, Fertilizacion, Riego, Temporada, dia_nominal
from gemelo.suelo import perfil_desde_soilgrids, perfil_manual

RAIZ = Path(__file__).resolve().parents[2]
REF = RAIZ / "datos" / "referencia"


@pytest.fixture(scope="session")
def clima_ames():
    return cargar_power(REF / "clima" / "power_ames_diario.csv")


@pytest.fixture(scope="session")
def suelo_ames():
    return perfil_desde_soilgrids(REF / "suelo" / "soilgrids_ames.json")


@pytest.fixture(scope="session")
def suelo_franco():
    return perfil_manual(arena=0.40, arcilla=0.20, mo_pct=2.5, cos_t_ha=60.0, cn_suelo=10.0)


def clima_constante(n_anios=2, precip=2.0, t=22.0, amplitud=8.0, rs=20.0, rh=60.0, viento=2.0, lat=10.0):
    """Clima sintético de prueba (no se usa para calibrar ni validar nada: solo para la física del motor)."""
    forma = (n_anios, 365)
    d = {"precip": np.full(forma, precip), "t2m": np.full(forma, t), "t2m_max": np.full(forma, t + amplitud / 2),
         "t2m_min": np.full(forma, t - amplitud / 2), "rad_sw": np.full(forma, rs), "rh2m": np.full(forma, rh),
         "ws2m": np.full(forma, viento)}
    return ClimaDiario(np.arange(2001, 2001 + n_anios), d, lat, 200.0, "sintético de prueba", naturaleza="simulado")


def maiz_continuo(anios=2, riego=None, n=150.0):
    return Estrategia("A", "Maíz continuo", [
        Temporada("maiz", dia_nominal(f"A{i}-03-01"), riego=riego or Riego(),
                  fertilizacion=[Fertilizacion(0, n)]) for i in range(1, anios + 1)])


def maiz_soya(anios=2):
    temps = [Temporada("maiz", dia_nominal("A1-03-01"), fertilizacion=[Fertilizacion(0, 150.0)]),
             Temporada("soya", dia_nominal("A2-03-01"))]
    return Estrategia("B", "Maíz-soya", temps[:anios])
