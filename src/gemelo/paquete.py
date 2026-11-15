# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
# asistido por SI: Claude Code (Opus 5.5), sensibilidad a la lluvia alterna IMERG (bloque 2)
"""Paquete estático por lote para la app pública sin servidor (contrato v1.1).

    <salida>/indice.json                      lista de lotes y archivos (rutas relativas a esta carpeta)
    <salida>/textos/en.json, es.json          catálogo de claves de texto
    <salida>/<lote_id>/simulacion_<tipo>.json y optimizacion_<tipo>.json   historico, seco, normal, humedo
    <salida>/<lote_id>/simulacion_<enso>.json                             enso_nino, enso_nina, enso_neutra
    <salida>/<lote_id>/personalizados/simulacion_dp<+d>_dt<+d>.json       grilla de los deslizadores
    <salida>/<lote_id>/calibracion/<id>.json                              ajustes de calibración típicos
    <salida>/<lote_id>/lote.json                                          entrada del lote en indice.json

La grilla y las calibraciones simulan un mismo conjunto comparable (estrategias del YAML más el frente de la
optimización histórica), para que los deslizadores reordenen siempre las mismas candidatas.
"""
import copy
import json
import shutil
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import yaml

from gemelo import tarjetas, textos
from gemelo.api import optimizar_con_ensamble, simular_con_ensamble
from gemelo.clima import con_precip_alterna
from gemelo.entrada import VERSION_CONTRATO, VERSION_CONTRATO_COMPLETA, leer_entrada, validar_lote_demo
from gemelo.salida import commit_git, limpiar

ESCENARIOS = ("historico", "seco", "normal", "humedo")
ESCENARIOS_ENSO = ("enso_nino", "enso_nina", "enso_neutra")
DELTA_PRECIP_PCT = (-30, -20, -10, 0, 10, 20, 30)
DELTA_TEMP_C = (0, 1, 2, 3)
CALIBRACIONES_POR_DEFECTO = {
    "n_inicial_bajo": {"descripcion": "Análisis de suelo con poco N mineral inicial",
                       "valores": {"cn.n_mineral_inicial_kg_ha": 15}},
    "n_inicial_alto": {"descripcion": "Análisis de suelo con mucho N mineral inicial",
                       "valores": {"cn.n_mineral_inicial_kg_ha": 50}},
    "suelo_seco_al_inicio": {"descripcion": "Humedad inicial medida baja (30 % del agua disponible)",
                             "valores": {"agua.fraccion_humedad_inicial": 0.3}},
    "suelo_humedo_al_inicio": {"descripcion": "Humedad inicial medida alta (80 % del agua disponible)",
                               "valores": {"agua.fraccion_humedad_inicial": 0.8}},
}
NOTA_NATURALEZA = ("metadatos.naturaleza = 'simulado' indica que el valor sale del modelo; no es SIMULADO "
                   "(dato ficticio) en el sentido del proyecto. El rótulo para mostrar es metadatos.rotulo.")


def _guardar(doc: dict, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")


def _rel(ruta: Path, raiz: Path) -> str:
    return ruta.relative_to(raiz).as_posix()


def exportar_textos(salida: Path) -> dict[str, str]:
    cat = textos.catalogo()
    rutas = {}
    for idioma, tabla in cat.items():
        r = salida / "textos" / f"{idioma}.json"
        r.parent.mkdir(parents=True, exist_ok=True)
        r.write_text(json.dumps(tabla, ensure_ascii=False, indent=1), encoding="utf-8")
        rutas[idioma] = _rel(r, salida)
    return rutas


INDICADORES_ALTERNA = ("produccion_relativa_anio", "deficit_relativo", "lixiviacion_n_kg_ha_anio",
                       "indice_exposicion_erosiva", "cambio_carbono_t_ha_anio")


def sensibilidad_lluvia_alterna(ent, doc: dict) -> dict | None:
    """Mismo histórico con la lluvia de IMERG: sensibilidad visible solo en modo técnico, nunca escenario equivalente.
    El contraste con la estación sale de comparacion_power_imerg.json de Datos."""
    alt = ent.precip_alterna
    if not alt:
        return None
    doc_alt, _ = simular_con_ensamble(replace(ent, clima=con_precip_alterna(ent.clima, alt["archivo"])))
    comp = next(x for x in json.loads(Path(alt["comparacion"]).read_text(encoding="utf-8"))
                if x["lote_id"] == ent.lote.id)
    c = next(v for k, v in comp.items() if k.startswith("contraste_estacion"))
    orden = {"power": doc["prioridades"]["pesos_iguales"]["orden"],
             "alterna": doc_alt["prioridades"]["pesos_iguales"]["orden"]}
    ind = {e["id"]: e["indicadores"] for e in doc["estrategias"]}
    return {"modo": "tecnico", "escenario_equivalente": False, "fuente_principal": "NASA POWER (PRECTOTCORR)",
            "fuente_alterna": doc_alt["clima"]["fuente"],
            "alineacion": "día UTC de IMERG sin realinear al día solar de POWER (desfase de hasta un día)",
            "precip_anual_media_mm": {"power": doc["clima"]["precip_anual_media_mm"],
                                      "alterna": doc_alt["clima"]["precip_anual_media_mm"]},
            "contraste_estacion": {"estacion": c["estacion"], "n_dias_comunes": c["n_dias_comunes_con_pluviometro"],
                                   "anual_equiv_mm": c["anual_equiv_en_dias_comunes_mm"],
                                   "sesgo_relativo_power": c["sesgo_relativo_power_vs_ghcn"],
                                   "sesgo_relativo_imerg": c["sesgo_relativo_imerg_vs_ghcn"],
                                   **{k: c[k] for k in ("fraccion_dias_usados", "fraccion_dias_con_dato",
                                                        "totales_mm_en_dias_comunes", "metodo_anual_equiv") if k in c}},
            "fuente_contraste": Path(alt["comparacion"]).name,
            "orden_pesos_iguales": orden,
            "posiciones": {i: {"central": orden["power"].index(i) + 1, "alterna": orden["alterna"].index(i) + 1}
                           for i in orden["power"]},
            "indicadores_p50": {e["id"]: {k: {"power": ind[e["id"]][k]["p50"], "alterna": e["indicadores"][k]["p50"]}
                                          for k in INDICADORES_ALTERNA if k in e["indicadores"]}
                                for e in doc_alt["estrategias"]}}


def _nombre_grilla(dp: float, dt: float) -> str:
    return f"simulacion_dp{int(dp):+d}_dt{int(dt):+d}.json"


def construir_lote(escenario_yaml: str | Path, lote_id: str, salida: str | Path, provisional: bool = True,
                   registro=print) -> dict:
    """Corre todo el paquete de un lote y devuelve su entrada para indice.json."""
    ruta = Path(escenario_yaml)
    base = ruta.resolve().parent
    raiz = Path(salida)
    validar_lote_demo(lote_id)
    d0 = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    cfg = d0.pop("paquete", None) or {}
    d0["lote"] = {**d0.get("lote", {}), "id": lote_id}
    escenarios = tuple(cfg.get("escenarios", ESCENARIOS))
    escenarios_enso = tuple(cfg.get("escenarios_enso", ESCENARIOS_ENSO))
    ejes = {"delta_precip_pct": list(cfg.get("delta_precip_pct", DELTA_PRECIP_PCT)),
            "delta_temp_c": list(cfg.get("delta_temp_c", DELTA_TEMP_C))}
    n_param_grilla = cfg.get("n_parametros_grilla")
    calibraciones = cfg.get("calibraciones_tipicas", CALIBRACIONES_POR_DEFECTO)
    hacer_sens = bool(cfg.get("sensibilidad", True))
    miembros_sens = int(cfg.get("miembros_clima_sensibilidad", 4))
    carpeta = raiz / lote_id
    if carpeta.exists():
        shutil.rmtree(carpeta)

    def entrada(tipo: str, calibracion: dict | None = None, n_parametros: int | None = None, **esc):
        d = copy.deepcopy(d0)
        e = {**(d.get("escenario") or {}), "tipo": tipo, **esc}
        if tipo not in ("historico", "personalizado"):
            e.pop("anio_inicio", None)
        d["escenario"] = e
        if calibracion:
            d["calibracion"] = {**(d.get("calibracion") or {}), **calibracion}
        if n_parametros:
            d["simulacion"] = {**(d.get("simulacion") or {}), "n_parametros": int(n_parametros)}
        ent = leer_entrada(d, base)
        ent.origen["archivo"] = ruta.as_posix()
        return ent

    def sens(ent, estrategias, objetivos=None):
        """Referencia: la de `simulacion` en las simulaciones; la línea base (primera) en las optimizaciones."""
        if not hacer_sens:
            return None
        ids_ = [e.id for e in estrategias]
        ref_id = ent.simulacion.get("referencia")
        ref = ids_.index(ref_id) if objetivos is None and ref_id in ids_ else 0
        return tarjetas.sensibilidad_supuestos(ent, estrategias, ref, miembros_sens, objetivos)

    def escribir(doc, sensibilidad, ruta_doc):
        if sensibilidad is not None:
            doc["sensibilidad_supuestos"] = limpiar(sensibilidad)
            doc["tarjetas"] = tarjetas.construir(doc, sensibilidad)
        _guardar(doc, ruta_doc)
        return _rel(ruta_doc, raiz)

    lote = {"lote_id": lote_id, "provisional": provisional, "escenario_origen": ruta.as_posix(),
            "escenarios": {}, "escenarios_enso": {}}
    ent_hist = entrada("historico")
    lote.update({k: getattr(ent_hist.lote, k) for k in ("nombre", "unidad_id", "lat", "lon")},
                clima_tipo=ent_hist.clima_lote)
    sens_sim = sens(ent_hist, ent_hist.estrategias)
    frente_hist = []
    for tipo in escenarios:
        registro(f"[{lote_id}] {tipo}: simulación")
        ent = ent_hist if tipo == "historico" else entrada(tipo)
        doc, _ = simular_con_ensamble(ent)
        if tipo == "historico":
            alt = sensibilidad_lluvia_alterna(ent, doc)
            if alt:
                doc["sensibilidad_precipitacion_alterna"] = limpiar(alt)
            lote["huella_parametros"] = doc["metadatos"]["huella_parametros"]
            lote["rotulo"] = doc["metadatos"]["rotulo"]
        archivos = {"simulacion": escribir(doc, sens_sim, carpeta / f"simulacion_{tipo}.json")}
        if ent.optimizacion:
            registro(f"[{lote_id}] {tipo}: optimización")
            doc_o, ens_o = optimizar_con_ensamble(ent)
            ests = [p.estrategia for p in ens_o.programas]
            if tipo == "historico":
                frente_hist = ests[1:]
            archivos["optimizacion"] = escribir(doc_o, sens(ent, ests, [o["id"] for o in doc_o["objetivos"]
                                                                        if o["id"] != "costo"]),
                                                carpeta / f"optimizacion_{tipo}.json")
        lote["escenarios"][tipo] = archivos
    for tipo in escenarios_enso:
        registro(f"[{lote_id}] {tipo}: simulación")
        try:
            ent = entrada(tipo)
        except ValueError as err:
            lote["escenarios_enso"][tipo] = {"omitido": str(err)}
            continue
        doc, _ = simular_con_ensamble(ent)
        lote["escenarios_enso"][tipo] = {"simulacion": escribir(doc, sens_sim, carpeta / f"simulacion_{tipo}.json"),
                                         "anios_analogos": doc["escenario"].get("anios_analogos")}

    comparables = list(ent_hist.estrategias) + frente_hist
    ids = [e.id for e in comparables]
    sens_comb = sens(replace(ent_hist, estrategias=comparables), comparables)
    lote["conjunto_comparable"] = {"estrategias": ids, "descripcion": "estrategias del escenario más el frente de "
                                                                      "la optimización histórica"}
    grilla = []
    for dp in ejes["delta_precip_pct"]:
        for dt in ejes["delta_temp_c"]:
            registro(f"[{lote_id}] personalizado dp={dp:+} dt={dt:+}")
            ent = replace(entrada("personalizado", n_parametros=n_param_grilla, delta_precip_pct=dp,
                                  delta_temp_c=dt), estrategias=comparables)
            doc, _ = simular_con_ensamble(ent)
            grilla.append({"delta_precip_pct": dp, "delta_temp_c": dt,
                           "archivo": escribir(doc, sens_comb, carpeta / "personalizados" / _nombre_grilla(dp, dt))})
    lote["personalizados"] = {"ejes": ejes, "patron": f"{lote_id}/personalizados/simulacion_dp{{dp:+d}}_dt{{dt:+d}}.json",
                              "n_parametros": int(n_param_grilla or ent_hist.simulacion["n_parametros"]),
                              "estrategias": ids, "archivos": grilla}
    lote["calibraciones"] = []
    for cid, c in calibraciones.items():
        registro(f"[{lote_id}] calibración {cid}")
        ent = replace(entrada("historico", calibracion=c["valores"]), estrategias=comparables)
        doc, _ = simular_con_ensamble(ent)
        lote["calibraciones"].append({"id": cid, "descripcion": c.get("descripcion", ""), "valores": c["valores"],
                                      "archivo": escribir(doc, sens_comb, carpeta / "calibracion" / f"{cid}.json")})
    lote["generado_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lote = limpiar(lote)
    (carpeta / "lote.json").write_text(json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
    return lote


def actualizar_indice(salida: str | Path) -> Path:
    """indice.json a partir de las carpetas <lote_id>/lote.json (permite construir lotes en paralelo)."""
    raiz = Path(salida)
    ruta = raiz / "indice.json"
    lotes = [json.loads(p.read_text(encoding="utf-8")) for p in raiz.glob("*/lote.json")]
    indice = {"version_contrato": VERSION_CONTRATO, "version_contrato_completa": VERSION_CONTRATO_COMPLETA,
              "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "commit": commit_git(),
              "nota_naturaleza": NOTA_NATURALEZA, "textos": exportar_textos(raiz),
              "escenarios": list(ESCENARIOS), "escenarios_enso": list(ESCENARIOS_ENSO),
              "lotes": sorted(lotes, key=lambda x: x["lote_id"])}
    ruta.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    return ruta


def construir(escenario_yaml: str | Path, lote_id: str, salida: str | Path, provisional: bool = True,
              registro=print) -> Path:
    construir_lote(escenario_yaml, lote_id, salida, provisional, registro)
    return actualizar_indice(salida)
