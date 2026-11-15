# asistido por SI: Claude Code (Anthropic), prueba de que el Gemelo nunca emite estrategias con objetivos de prioridad faltantes (D-039, C-4)
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PAQUETES = RAIZ / "datos" / "publicos" / "gemelo"
CASOS = RAIZ / "contratos" / "prioridades_casos.json"


def objetivos_de_prioridad() -> list[str]:
    # los objetivos salen del contrato (gemelo_api §4), no de una lista escrita aquí
    d = json.loads(CASOS.read_text(encoding="utf-8"))["deslizadores"]
    return sorted({o for os_ in d.values() for o in os_})


def faltantes(doc: dict, objetivos: list[str]) -> list[tuple[str, str]]:
    """(id de estrategia, objetivo) sin valor numérico finito en `metricas`."""
    ests = list(doc.get("estrategias") or []) + list(doc.get("frente") or [])
    if isinstance(doc.get("linea_base"), dict):
        ests.append(doc["linea_base"])
    malos = []
    for e in ests:
        m = e.get("metricas") or {}
        for o in objetivos:
            v = m.get(o)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
                malos.append((str(e.get("id")), o))
    return malos


def test_el_detector_ve_un_objetivo_faltante():
    obj = objetivos_de_prioridad()
    completo = {o: 1.0 for o in obj}
    doc = {"estrategias": [{"id": "A", "metricas": completo}, {"id": "B", "metricas": {**completo, obj[0]: None}}]}
    assert faltantes(doc, obj) == [("B", obj[0])]


def test_ningun_paquete_publicado_tiene_objetivos_de_prioridad_faltantes():
    obj = objetivos_de_prioridad()
    assert len(obj) == 6
    revisadas, malos = 0, []
    for f in sorted(PAQUETES.rglob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            continue
        n = len(doc.get("estrategias") or []) + len(doc.get("frente") or []) + isinstance(doc.get("linea_base"), dict)
        if not n or not any("metricas" in e for e in (doc.get("estrategias") or []) + (doc.get("frente") or [])):
            continue
        revisadas += n
        malos += [(f.relative_to(PAQUETES).as_posix(), *x) for x in faltantes(doc, obj)]
    assert revisadas > 0
    assert malos == [], malos[:5]
