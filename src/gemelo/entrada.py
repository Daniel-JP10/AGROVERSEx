# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Lectura del escenario de entrada (YAML o dict con el esquema de contratos/gemelo_api.md) a objetos del gemelo."""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from gemelo.clima import ClimaDiario, cargar_power, desagregar_mensual, mensual_desde_sqlite
from gemelo.escenarios import EscenarioClimatico, construir
from gemelo.modelos import Estrategia, Fertilizacion, Lote, Riego, Temporada, dia_nominal
from gemelo.suelo import PerfilSuelo, perfil_desde_soilgrids, perfil_manual

VERSION_CONTRATO = 1


@dataclass
class Entrada:
    lote: Lote
    clima_lote: str                      # templado | tropical (para las reglas de sucesión)
    clima: ClimaDiario
    suelo: PerfilSuelo
    escenario: EscenarioClimatico
    estrategias: list[Estrategia]
    simulacion: dict
    calibracion: dict
    costos: dict | None
    optimizacion: dict | None
    origen: dict = field(default_factory=dict)


def _ruta(valor: str, base: Path) -> Path:
    """Ruta relativa al archivo YAML; si no existe ahí, relativa al directorio de trabajo."""
    p = Path(valor)
    if p.is_absolute():
        return p
    return base / p if (base / p).exists() else Path.cwd() / p


def _temporada(d: dict) -> Temporada:
    r = d.get("riego") or {}
    return Temporada(
        cultivo=d["cultivo"], siembra=dia_nominal(d["siembra"]),
        etapas=tuple(d["etapas"]) if d.get("etapas") else None, etapas_variante=d.get("etapas_variante"),
        riego=Riego(r.get("modo", "ninguno"), float(r.get("umbral", 1.0)), r.get("tope_mm")),
        fertilizacion=[Fertilizacion(int(f["dia"]), float(f["kg_n"])) for f in d.get("fertilizacion", [])],
        cosechar=bool(d.get("cosechar", True)), residuos=d.get("residuos", "superficie"),
        labranza_siembra=bool(d.get("labranza_siembra", False)))


def estrategia_desde_dict(d: dict) -> Estrategia:
    return Estrategia(str(d["id"]), d.get("nombre", str(d["id"])), [_temporada(t) for t in d["temporadas"]],
                      d.get("descripcion", ""), d.get("etiqueta", "ilustrativa"))


def _clima(d: dict, base: Path, semilla: int) -> ClimaDiario:
    fuente = d.get("fuente", "power_csv")
    if fuente == "power_csv":
        return cargar_power(_ruta(d["archivo"], base))
    if fuente == "sqlite_mensual":
        mensual, anios, lat = mensual_desde_sqlite(_ruta(d["ruta"], base), d["unidad_id"])
        if "elevacion_m" not in d:
            raise ValueError("clima sqlite_mensual: falta elevacion_m (la necesita Penman-Monteith)")
        return desagregar_mensual(mensual, anios, float(d.get("lat", lat)), float(d["elevacion_m"]), semilla,
                                  fuente=f"agroversex.sqlite tabla mensual ({d['unidad_id']}), desagregado a diario")
    raise ValueError(f"clima.fuente {fuente!r}: power_csv o sqlite_mensual")


def _suelo(d: dict, base: Path) -> PerfilSuelo:
    fuente = d.get("fuente", "soilgrids_json")
    if fuente == "soilgrids_json":
        return perfil_desde_soilgrids(_ruta(d["archivo"], base), d.get("profundidad_m"))
    if fuente == "manual":
        return perfil_manual(float(d["arena"]), float(d["arcilla"]), float(d["mo_pct"]), float(d["cos_t_ha"]),
                             d.get("cn_suelo"), float(d.get("profundidad_m", 1.0)))
    raise ValueError(f"suelo.fuente {fuente!r}: soilgrids_json o manual")


def leer_entrada(fuente: str | Path | dict, base: Path | None = None) -> Entrada:
    if isinstance(fuente, dict):
        d, base = fuente, base or Path.cwd()
    else:
        ruta = Path(fuente)
        with open(ruta, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        base = ruta.resolve().parent
    v = d.get("version_contrato", VERSION_CONTRATO)
    if int(v) > VERSION_CONTRATO:
        raise ValueError(f"version_contrato {v} más nueva que la que entiende este gemelo ({VERSION_CONTRATO})")
    lo = d.get("lote", {})
    lote = Lote(str(lo.get("id", "lote")), lo.get("nombre", ""), float(lo.get("lat", 0.0)), float(lo.get("lon", 0.0)),
                lo.get("unidad_id"), lo.get("finca_id"), lo.get("geometria_wkt"), lo.get("area_ha"),
                lo.get("zona_demo"))
    sim = {"n_parametros": 8, "semilla": 42, "n_sub": 1, "equilibrio": "completo", "referencia": None,
           **(d.get("simulacion") or {})}
    clima = _clima(d["clima"], base, int(sim["semilla"]))
    e = d.get("escenario", {})
    esc = construir(clima, e.get("tipo", "historico"), int(e.get("anios", 3)), int(e.get("semilla", 0)),
                    e.get("n_miembros"), e.get("anio_inicio"), float(e.get("delta_precip_pct", 0.0)),
                    float(e.get("delta_temp_c", 0.0)), e.get("max_miembros"))
    estrategias = [estrategia_desde_dict(x) for x in d.get("estrategias", [])]
    ids = [x.id for x in estrategias]
    if len(set(ids)) != len(ids):
        raise ValueError(f"ids de estrategia repetidos: {ids}")
    return Entrada(lote, lo.get("clima_tipo", "templado"), clima, _suelo(d["suelo"], base), esc, estrategias, sim,
                   dict(d.get("calibracion") or {}), d.get("costos"), d.get("optimizacion"),
                   {"archivo": str(fuente) if not isinstance(fuente, dict) else None})
