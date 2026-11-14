# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import re
from pathlib import Path

import pandas as pd
import pytest
import yaml

from simulacion import config
from simulacion.referencias import cargar as ref

RAIZ = config.RAIZ
REPORTES = RAIZ / "evidencia" / "reportes"
REFERENCIAS = RAIZ / "src" / "simulacion" / "referencias"

CLI = "INV-CLI_anclas_reales_2000_2026.md"
ROT = "INV-ROT_rotaciones_y_nichos.md"
ENS = "INV-ENS_teleconexiones_enso.md"

SIN_DATO = ("s.d.", "n.d.", "NA", "PENDIENTE", "descartado", "—")


# Analizador independiente de los reportes: no reutiliza cargar.py.
def _tabla(reporte, marca):
    # Filas de la primera tabla Markdown bajo el título que contiene `marca`
    lineas = (REPORTES / reporte).read_text(encoding="utf-8").splitlines()
    inicio = next(n for n, l in enumerate(lineas) if l.startswith("#") and marca in l)
    filas = []
    for linea in lineas[inicio + 1:]:
        if linea.startswith("|"):
            filas.append([c.strip() for c in linea.strip().strip("|").split("|")])
        elif linea.startswith("#") and not filas:
            raise AssertionError(f"sin tabla bajo '{marca}'")
        elif filas:
            break
    assert len(filas) >= 3, f"tabla vacía bajo '{marca}'"
    return filas[2:]  # sin encabezado ni separador


def _num(celda):
    if celda.startswith(SIN_DATO):
        return None
    return float(celda.replace("−", "-").replace(",", ".").replace("*", "").strip())


def _yaml(nombre):
    return yaml.safe_load((REFERENCIAS / nombre).read_text(encoding="utf-8"))


def _registros(obj):
    # Todo dict que lleve "etiqueta" es un registro de referencia
    if isinstance(obj, dict):
        if "etiqueta" in obj:
            yield obj
        for v in obj.values():
            yield from _registros(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _registros(v)


SIN_EVIDENCIA = pytest.mark.skipif(not REPORTES.exists(), reason="sin carpeta evidencia/reportes")


# Transcripción: cada YAML contra su tabla del reporte, celda a celda.

@SIN_EVIDENCIA
def test_todo_registro_tiene_fuente():
    prefijos = {p.name.split("_")[0]: p for p in REPORTES.glob("INV-*.md")}
    fallas = []
    for ruta in sorted(REFERENCIAS.glob("*.yaml")):
        for reg in _registros(yaml.safe_load(ruta.read_text(encoding="utf-8"))):
            fid, informe = reg.get("fuente_id"), reg.get("fuente_informe")
            if fid is not None and not (RAIZ / "evidencia" / f"{fid}.yaml").exists():
                fallas.append((ruta.name, "fuente_id inexistente", fid))
            if fid is None and not informe:
                fallas.append((ruta.name, "sin fuente_id ni fuente_informe", reg.get("etiqueta")))
            if informe:
                m = re.match(r"INV-[A-Za-z0-9]+", informe)
                if not m or m.group(0) not in prefijos:
                    fallas.append((ruta.name, "reporte inexistente", informe))
                    continue
                s = re.search(r"§([\d.]+)", informe)
                if s:
                    texto = prefijos[m.group(0)].read_text(encoding="utf-8")
                    if not re.search(rf"^#+ {re.escape(s.group(1))}[.\s]", texto, re.M):
                        fallas.append((ruta.name, "sección inexistente", informe))
    assert fallas == []


@SIN_EVIDENCIA
def test_enso_transcripcion_contra_reporte():
    # Cada fila del YAML es un año con 12 temporadas (DJF..NDJ) en orden de mes central
    for nombre, marca in (("oni", "1.3 Tabla ONI"), ("roni", "1.4 Tabla RONI")):
        esperado = {int(f[0]): [_num(c) for c in f[1:13]] for f in _tabla(CLI, marca)}
        real = {r["anio"]: r["valores"] for r in _yaml("enso.yaml")[nombre]}
        assert len(esperado) == 27
        assert real == esperado, nombre


def test_enso_valores_ancla():
    df = ref.cargar_enso()
    assert len(df) == 323
    aso_2026 = (2026 - 2000) * 12 + 8  # septiembre de 2026, centro de ASO
    assert df.loc[aso_2026, "oni"] == pytest.approx(2.46)
    assert df.loc[aso_2026, "roni"] == pytest.approx(1.97)
    posteriores = df[df["mes_id"] > aso_2026]
    assert posteriores[["oni", "roni"]].isna().all().all()


def test_eventos_solo_fuente():
    eventos = ref.cargar_eventos()
    assert eventos and all(e["etiqueta"] == "FUENTE" for e in eventos)
    assert not any(e["region_texto"] == "Europa" and e["inicio"] == 2003 for e in eventos)


@SIN_EVIDENCIA
def test_eventos_cuentan_los_fuente():
    filas = _tabla(CLI, "Catálogo de 34 eventos")
    assert len(filas) == 34
    esperados = sum(1 for f in filas if f[6].startswith("FUENTE"))
    assert len(ref.cargar_eventos()) == esperados


@SIN_EVIDENCIA
def test_eventos_transcripcion():
    filas = [f for f in _tabla(CLI, "Catálogo de 34 eventos")]
    real = {e["id"]: e for e in yaml.safe_load(
        (REFERENCIAS / "eventos.yaml").read_text(encoding="utf-8"))["eventos"]}
    assert len(real) == 34
    for f in filas:
        e = real[f"ev{int(f[0]):02d}"]
        assert (e["tipo"], e["fecha_texto"], e["region_texto"], e["magnitud_texto"], e["url"]) == (
            f[1], f[2], f[3], f[4], f[5])
        assert e["estado_texto"] == f[6]


def test_kluger_34_filas():
    assert len(ref.cargar_kluger()) == 34


@SIN_EVIDENCIA
def test_kluger_transcripcion():
    # la tabla de evidencia trae 36 filas; las 2 de China no se cargan (§5.1)
    filas = [f for f in _tabla(ROT, "2. Efecto del cultivo") if f[0] != "China"]
    df = ref.cargar_kluger()
    assert len(filas) == len(df) == 34
    for f, (_, r) in zip(filas, df.iterrows()):
        antecesor, cultivo = f[1].split("→")
        assert (r["pais"], r["antecesor"], r["cultivo"]) == (f[0], antecesor, cultivo)
        for col, celda in (("efecto2", f[2]), ("eff_div", f[3]),
                           ("beta_lluvia", f[4]), ("beta_t", f[5])):
            valor = _num(celda)
            if valor is None:
                assert pd.isna(r[col]), (f, col)
            else:
                assert r[col] == pytest.approx(valor), (f, col)
        assert r["sig_efecto2"] == ("*" in f[2])
        assert r["sig_beta_t"] == ("*" in f[5])


def test_kluger_sin_filas_ni_columna_de_procedencia_china():
    k = ref.cargar_kluger()
    assert len(k) == 34
    assert "China" not in set(k["pais"])
    assert "procedencia_china" not in k.columns


def test_teleconexiones_sin_coeficiente_de_procedencia_china():
    t = ref.cargar_teleconexiones()
    assert "coef_mm_dia" not in t.columns and "meses_coef" not in t.columns
    txt = (Path(ref.__file__).parent / "teleconexiones.yaml").read_text(encoding="utf-8").lower()
    assert "procedencia" not in txt and "coef_mm_dia" not in txt


def test_fao56_15_cultivos_13_con_agua():
    df = ref.cargar_fao56()
    assert len(df) == 15
    assert df["agua_min"].notna().sum() == 13
    sin_agua = df[df["agua_min"].isna()]
    assert set(sin_agua["cultivo"]) == {"Café", "Trébol berseem"}
    assert set(sin_agua["etiqueta_agua"]) == {"PENDIENTE"}


@SIN_EVIDENCIA
def test_fao56_transcripcion():
    filas = [f for f in _tabla(ROT, "3. Parámetros FAO-56") if f[5]]  # sin Zr: no está en FAO-56
    df = ref.cargar_fao56().set_index("cultivo")
    assert len(filas) == 15
    for f in filas:
        r = df.loc[f[0]]
        assert r["kc_ini"] == f[1]
        assert r["kc_mid"] == f[2]
        assert r["kc_end"] == f[3]
        assert r["etapas"] == f[4]
        zr = [float(x.replace(",", ".")) for x in re.findall(r"\d+,\d+", f[5])]
        assert (r["zr_min"], r["zr_max"]) == (zr[0], zr[-1])
        assert r["p"] == pytest.approx(float(re.search(r"\d+,\d+", f[6]).group(0).replace(",", ".")))
        agua = re.findall(r"\d+", f[7])
        if agua:
            assert (r["agua_min"], r["agua_max"]) == (float(agua[0]), float(agua[1]))
        else:
            assert pd.isna(r["agua_min"])


def test_faostat_colombia():
    df = ref.cargar_faostat()
    def valor(cultivo, periodo):
        fila = df[(df["pais"] == "Colombia") & (df["cultivo"] == cultivo) & (df["periodo"] == periodo)]
        return float(fila["media"].iloc[0])
    assert valor("Maíz", "2000-2004") == pytest.approx(2.35)
    assert valor("Maíz", "2020-2024") == pytest.approx(4.11)
    assert valor("Papa", "2000-2004") == pytest.approx(15.02)
    assert valor("Papa", "2020-2024") == pytest.approx(22.08)


@SIN_EVIDENCIA
def test_faostat_transcripcion():
    cultivos = ["Maíz", "Trigo", "Arroz", "Soja", "Frijol", "Papa", "Café", "Caña", "Sorgo", "Mijo"]
    filas = _tabla(CLI, "7.3 Rendimiento")
    df = ref.cargar_faostat()
    df = df[df["periodo"] == "2020-2024"]
    assert len(filas) == 15
    for f in filas:
        for cultivo, celda in zip(cultivos, f[1:11]):
            r = df[(df["pais"] == f[0]) & (df["cultivo"] == cultivo)].iloc[0]
            m = re.match(r"^([\d.]+) \(([\d.]+)-([\d.]+)\)$", celda)
            if m:
                assert (r["media"], r["minimo"], r["maximo"]) == (
                    pytest.approx(float(m.group(1))), float(m.group(2)), float(m.group(3)))
            else:
                assert pd.isna(r["media"]), (f[0], cultivo)


def test_teleconexiones_solo_dos_fuentes():
    df = ref.cargar_teleconexiones()
    assert len(df) == 9  # 3 de INV-ENS y 6 de R-1b
    assert df["estado"].str.startswith("2 fuentes").all()
    assert df["coef"].isna().all()


@SIN_EVIDENCIA
def test_teleconexiones_transcripcion():
    filas = [f for f in _tabla(ENS, "Tabla") if f[7].startswith("2 fuentes")]
    df = ref.cargar_teleconexiones()
    df = df[df.fuente_informe.str.startswith("INV-ENS")]  # las de R-1b no están en ese reporte
    assert len(filas) == len(df) == 3
    for f, (_, r) in zip(filas, df.iterrows()):
        assert (r["macroregion"], r["variable"], r["signo_nino"], r["signo_nina"], r["estado"]) == (
            f[0], f[2], f[3], f[4], f[7])


def test_berkeley_colombia():
    assert ref.cargar_berkeley()["Colombia"] == 0.240


@SIN_EVIDENCIA
def test_berkeley_transcripcion():
    filas = _tabla(CLI, "2.2 Tasas regionales")
    datos = ref.cargar_berkeley()
    assert len(filas) == len(datos) > 0
    for f in filas:
        assert datos[f[0]] == pytest.approx(_num(f[3]))


def test_gistemp_anual_y_transcripcion():
    serie = ref.cargar_gistemp_anual()
    assert list(serie.index) == list(range(2000, 2026))
    assert serie.loc[2000] == pytest.approx(0.39)
    assert serie.loc[2025] == pytest.approx(1.18)
    if not REPORTES.exists():
        return
    filas = _tabla(CLI, "2.3 Anomalías globales")
    assert len(filas) == len(serie) > 0
    for f in filas:
        assert serie.loc[int(f[0])] == pytest.approx(_num(f[1]))


def test_gistemp_tendencia_inferencia():
    tendencia = ref.cargar_gistemp_tendencia()
    assert tendencia["etiqueta"] == "INFERENCIA"
    assert tendencia["valor"] == pytest.approx(0.326)


@SIN_EVIDENCIA
def test_rodell_transcripcion():
    filas = _tabla(CLI, "5.1 Rodell")
    df = ref.cargar_rodell()
    assert len(df) == 34 > len(filas)  # R-1b completó las 34 áreas (EV-ENS-017)
    for f in filas:
        valor, incert = f[1].split("±")
        (r,) = df[df.region.str.startswith(f[0].split(" (")[0])].iloc[:1].itertuples()
        assert r.gt_anio == pytest.approx(_num(valor))
        assert r.incertidumbre == pytest.approx(_num(incert))
    assert not df["cm_anio"].isna().any()
    assert (df.cm_anio - df.gt_anio / df.area_km2 * 1e5).abs().max() < 0.01


@SIN_EVIDENCIA
def test_sistemas_rotacion_transcripcion():
    filas = _tabla(ROT, "6. Sistemas de rotación")
    real = _yaml("sistemas_rotacion.yaml")["sistemas"]
    assert len(filas) == len(real) > 0
    # R-4 reescribió 9 regiones; solo las de INV-ROT (Corn Belt, Indo-Gangética) se comparan con su reporte
    real = [r for r in real if r["fuente_informe"].startswith("INV-ROT")]
    filas = [f for f in filas if f[0] in {r["region"] for r in real}]
    assert len(real) == len(filas) == 2
    for f, r in zip(filas, real):
        assert (r["region"], r["habitual"], r["alternativa_1"], r["alternativa_2"]) == tuple(f[:4])
        assert r["fuente_texto"] == f[4]


@SIN_EVIDENCIA
def test_sucesion_transcripcion():
    filas = _tabla(ROT, "5.1 Clima templado")
    real = _yaml("sucesion.yaml")["reglas"]
    assert len(filas) == len(real) > 0
    real, orig = [r for r in real if r["fuente_informe"].startswith("INV-ROT")], real
    filas = [f for f, r in zip(filas, orig) if r["fuente_informe"].startswith("INV-ROT")]
    assert 0 < len(real) == len(filas) < len(orig)  # el resto lo fijó R-4 (tabla 2)
    for f, r in zip(filas, real):
        assert (r["cultivo_o_familia"], r["enfermedad"], r["intervalo_texto"]) == (f[0], f[1], f[2])
        assert r["fuente_texto"] == f[3]


def test_africa_enso_sin_cai_2025_y_con_cita_cpc():
    # D-024: el signo de ENSO en África sale de NOAA CPC, no de Cai 2025
    txt = (Path(ref.__file__).parent / "teleconexiones.yaml").read_text(encoding="utf-8")
    assert "Cai 2025" not in txt and "EV-ENS-009" not in txt
    t = ref.cargar_teleconexiones().set_index("macroregion")
    for r in ("Sureste de África", "Cuerno de África"):
        assert "CPC-ASSESS97-AFRICA" in t.loc[r, "fuentes"]
    assert "Cai 2025" not in (Path(config.RAIZ) / "src/simulacion/clima.py").read_text(encoding="utf-8")
