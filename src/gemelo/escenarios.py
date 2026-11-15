# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
# asistido por SI: Claude Code (Opus 5.5), bloque 2: alerta de helada D-032, lluvia alterna IMERG y avisos del suelo calibrado
"""Escenarios climáticos e(t) construidos con años reales del registro histórico.

- historico: ventanas consecutivas de H años del registro (una por año de inicio) o un año de inicio fijo.
- seco / normal / humedo: cada año simulado toma un año análogo cuya lluvia anual está cerca del percentil
  20 / 50 / 80 del registro. No se reescalan series: se conservan secuencias diarias reales.
- personalizado: ventanas históricas con cambio porcentual de lluvia y desplazamiento de temperatura.
Ningún escenario es un pronóstico climático.
"""
from dataclasses import dataclass, field

import numpy as np

from gemelo.clima import ClimaDiario, calcular_eto
from gemelo.enso import AVISO_INTERINO, fases_por_anio

PERCENTIL_TIPO = {"seco": 20.0, "normal": 50.0, "humedo": 80.0}
AVISO_HIPOTETICO = ("Escenario hipotético construido con años históricos reales; no es un pronóstico ni una "
                    "proyección climática oficial.")
AVISO_HISTORICO = ("Clima histórico real en ventanas de varios años: describe la variabilidad pasada del lugar, "
                   "no garantiza la futura.")


@dataclass
class EscenarioClimatico:
    tipo: str
    anios_horizonte: int
    miembros: list[list[int]]           # índices de año (en ClimaDiario.anios) para cada año simulado
    delta_precip_pct: float = 0.0
    delta_temp_c: float = 0.0
    aviso: str = ""
    detalle: dict = field(default_factory=dict)

    @property
    def n_miembros(self) -> int:
        return len(self.miembros)

    def a_dict(self, clima: ClimaDiario) -> dict:
        return {"tipo": self.tipo, "anios_horizonte": self.anios_horizonte, "n_miembros": self.n_miembros,
                "anios_por_miembro": [[int(clima.anios[i]) for i in m] for m in self.miembros],
                "delta_precip_pct": self.delta_precip_pct, "delta_temp_c": self.delta_temp_c,
                "aviso": self.aviso, "naturaleza": "simulado" if self.tipo != "historico" else clima.naturaleza,
                **self.detalle}


TIPOS_ENSO = {"enso_nino": "nino", "enso_nina": "nina", "enso_neutra": "neutra"}


def construir(clima: ClimaDiario, tipo: str, anios_horizonte: int, semilla: int = 0, n_miembros: int | None = None,
              anio_inicio: int | None = None, delta_precip_pct: float = 0.0, delta_temp_c: float = 0.0,
              max_miembros: int | None = None, enso_archivo: str | None = None) -> EscenarioClimatico:
    n, H = clima.n_anios, anios_horizonte
    if H < 1:
        raise ValueError("el horizonte debe tener al menos un año")
    rng = np.random.default_rng(semilla)
    if tipo in TIPOS_ENSO:
        fases, meta = fases_por_anio(enso_archivo)
        fase = TIPOS_ENSO[tipo]
        banda = [i for i, a in enumerate(clima.anios) if fases.get(int(a)) == fase]
        if not banda:
            raise ValueError(f"escenario {tipo}: ningún año del registro clasificado como {fase}")
        m = n_miembros or max(len(banda), 5)
        miembros = [list(rng.choice(banda, size=H, replace=True)) for _ in range(m)]
        detalle = {"fase_enso": fase, "clasificacion_enso": meta,
                   "anios_analogos": sorted(int(clima.anios[i]) for i in banda),
                   "avisos": [AVISO_INTERINO] if meta["interina"] else []}
        return EscenarioClimatico(tipo, H, miembros, aviso=AVISO_HIPOTETICO, detalle=detalle)
    if tipo in ("historico", "personalizado"):
        if H > n:
            raise ValueError(f"horizonte de {H} años mayor que el registro ({n} años)")
        if anio_inicio is not None:
            i0 = int(np.where(clima.anios == anio_inicio)[0][0]) if anio_inicio in clima.anios else None
            if i0 is None or i0 + H > n:
                raise ValueError(f"año de inicio {anio_inicio} no permite {H} años completos")
            miembros = [list(range(i0, i0 + H))]
        else:
            miembros = [list(range(i, i + H)) for i in range(n - H + 1)]
        if max_miembros and len(miembros) > max_miembros:
            sel = np.linspace(0, len(miembros) - 1, max_miembros).round().astype(int)
            miembros = [miembros[i] for i in sel]
        aviso = AVISO_HISTORICO if tipo == "historico" else AVISO_HIPOTETICO
        if tipo == "historico" and (delta_precip_pct or delta_temp_c):
            raise ValueError("los cambios de lluvia o temperatura solo aplican al escenario personalizado")
        return EscenarioClimatico(tipo, H, miembros, delta_precip_pct, delta_temp_c, aviso)
    if tipo in PERCENTIL_TIPO:
        p_anual = clima.precip_anual()
        objetivo = np.percentile(p_anual, PERCENTIL_TIPO[tipo])
        k = max(3, int(round(n / 5)))
        banda = np.argsort(np.abs(p_anual - objetivo))[:k]
        m = n_miembros or max(k, 5)
        miembros = [list(rng.choice(banda, size=H, replace=True)) for _ in range(m)]
        detalle = {"percentil_objetivo": PERCENTIL_TIPO[tipo], "precip_anual_objetivo_mm": float(objetivo),
                   "anios_analogos": sorted(int(clima.anios[i]) for i in banda),
                   "precip_anual_analogos_mm": sorted(float(p_anual[i]) for i in banda)}
        return EscenarioClimatico(tipo, H, miembros, aviso=AVISO_HIPOTETICO, detalle=detalle)
    raise ValueError(f"tipo de escenario {tipo!r}: historico, seco, normal, humedo, personalizado, enso_nino, "
                     "enso_nina o enso_neutra")


def series(clima: ClimaDiario, esc: EscenarioClimatico, viento_respaldo: float = 2.0) -> tuple[dict, str]:
    """Series (K, 365 H) de precip, t2m, rad_sw, et0 (y el resto) para los K miembros del escenario."""
    idx = np.array(esc.miembros)                      # (K, H)
    K, H = idx.shape
    datos = {v: arr[idx] for v, arr in clima.datos.items()}   # (K, H, 365)
    if esc.delta_precip_pct:
        datos["precip"] = datos["precip"] * (1 + esc.delta_precip_pct / 100.0)
    if esc.delta_temp_c:
        for v in ("t2m", "t2m_max", "t2m_min", "t2m_min_corr"):
            if v in datos:
                datos[v] = datos[v] + esc.delta_temp_c
    if "t2m" not in datos:
        datos["t2m"] = (datos["t2m_max"] + datos["t2m_min"]) / 2
    if "rad_sw" not in datos:
        raise ValueError("falta radiación solar (rad_sw): la biomasa por RUE la necesita")
    et0, metodo = calcular_eto(datos, clima.lat, clima.elevacion_m, viento_respaldo)
    datos["et0"] = et0
    return {k: v.reshape(K, H * 365) for k, v in datos.items()}, metodo


def umbral_lluvia_intensa(clima: ClimaDiario, percentil: float = 90.0, minimo_mm: float = 1.0) -> float:
    """Percentil de la lluvia diaria en días húmedos (>= 1 mm) de todo el registro, mm/día."""
    p = clima.datos["precip"].reshape(-1)
    humedos = p[p >= minimo_mm]
    return float(np.percentile(humedos, percentil)) if humedos.size else float("inf")
