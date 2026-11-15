# asistido por SI: Claude Code (Anthropic), prueba de que los registros no tienen filas de tabla sueltas
# Falla si en LICENCIAS_TERCEROS.md, CITAS.md o SI_USO.md una fila de tabla (linea que empieza con |)
# aparece fuera de una tabla con encabezado y separador, o con distinto numero de columnas que su encabezado.
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
REGISTROS = ["LICENCIAS_TERCEROS.md", "CITAS.md", "SI_USO.md"]
SEPARADOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")


def _columnas(linea):
    # cuenta celdas: pipes sin escapar, fuera de codigo en linea
    sin_codigo = re.sub(r"`[^`]*`", "", linea.strip())
    return len(re.findall(r"(?<!\\)\|", sin_codigo)) - 1


def filas_sueltas(texto):
    """Devuelve lista de (numero_de_linea, motivo) con las filas fuera de una tabla valida."""
    lineas = texto.splitlines()
    errores = []
    en_codigo = False
    i = 0
    while i < len(lineas):
        if lineas[i].lstrip().startswith("```"):
            en_codigo = not en_codigo
        if en_codigo or not lineas[i].startswith("|"):
            i += 1
            continue
        # bloque contiguo de lineas que empiezan con |
        j = i
        while j < len(lineas) and lineas[j].startswith("|"):
            j += 1
        bloque = lineas[i:j]
        if len(bloque) < 2 or not SEPARADOR.match(bloque[1]):
            errores.append((i + 1, "fila sin encabezado y separador antes"))
        else:
            n = _columnas(bloque[0])
            for k, fila in enumerate(bloque[2:], start=i + 3):
                if _columnas(fila) != n:
                    errores.append((k, f"{_columnas(fila)} columnas y el encabezado tiene {n}"))
        i = j
    return errores


@pytest.mark.parametrize("nombre", REGISTROS)
def test_sin_filas_sueltas(nombre):
    errores = filas_sueltas((RAIZ / nombre).read_text(encoding="utf-8"))
    assert not errores, f"{nombre}: {errores[:10]} (total {len(errores)})"


def test_detecta_fila_tras_parrafo():
    texto = "Texto.\n\n| a | b |\n|-|-|\n| 1 | 2 |\n\nOtro parrafo\n| 3 | 4 |\n"
    assert filas_sueltas(texto) == [(8, "fila sin encabezado y separador antes")]


def test_detecta_fila_tras_lista():
    texto = "- item\n- otro\n| 3 | 4 |\n| 5 | 6 |\n"
    assert [e[0] for e in filas_sueltas(texto)] == [3]


def test_detecta_fila_tras_tabla_separada_por_blanco():
    texto = "| a | b |\n|-|-|\n| 1 | 2 |\n\n| 3 | 4 |\n"
    assert [e[0] for e in filas_sueltas(texto)] == [5]


def test_detecta_columnas_desiguales():
    assert len(filas_sueltas("| a | b |\n|-|-|\n| 1 | 2 | 3 |\n")) == 1


def test_tabla_valida_y_codigo_no_fallan():
    texto = "| a | b |\n|---|:-:|\n| 1 | `x|y` |\n\n```\n| suelta |\n```\n"
    assert filas_sueltas(texto) == []


def test_copia_con_filas_sueltas_de_evidencia_falla():
    # RED: la copia de evidencia tiene filas sueltas y debe ser detectada
    ruta = RAIZ / "datos" / "evidencia" / "S4_registros_con_filas_sueltas.md"
    assert len(filas_sueltas(ruta.read_text(encoding="utf-8"))) == 3
