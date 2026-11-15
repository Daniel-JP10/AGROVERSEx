# asistido por SI: Claude Code (Anthropic), pruebas de que el build de despliegue falla claro si falta AGROVERSEX_DATOS, teselas o índice (D-037 C2.2)
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mapa_estatico import construir as c

SRC = Path(__file__).resolve().parents[2] / "src"


def datos_falsos(raiz: Path) -> Path:
    for o in (*c.ARCHIVOS_DESPLIEGUE, "unidades.gpkg"):
        (raiz / o).parent.mkdir(parents=True, exist_ok=True)
        (raiz / o).write_bytes(b"x")
    return raiz


def correr(*args, **entorno):
    env = {k: v for k, v in os.environ.items() if k != "AGROVERSEX_DATOS"} | {"PYTHONPATH": str(SRC)} | entorno
    return subprocess.run([sys.executable, "-m", "mapa_estatico.construir", *args], capture_output=True, text=True, env=env)


def test_sin_variable_el_proceso_termina_con_error_claro(tmp_path):
    r = correr("--desplegar", str(tmp_path))
    assert r.returncode != 0
    assert "AGROVERSEX_DATOS" in r.stderr and "Traceback" not in r.stderr


def test_carpeta_inexistente(tmp_path):
    with pytest.raises(c.ErrorDespliegue, match="no existe"):
        c.raiz_datos({"AGROVERSEX_DATOS": str(tmp_path / "nada")})


@pytest.mark.parametrize("falta", ["teselas/adm2.pmtiles", "indice_busqueda.json.gz", "unidades.gpkg"])
def test_falta_un_archivo_y_se_nombra(tmp_path, falta):
    datos_falsos(tmp_path)
    (tmp_path / falta).unlink()
    with pytest.raises(c.ErrorDespliegue, match=falta):
        c.raiz_datos({"AGROVERSEX_DATOS": str(tmp_path)})
    r = correr("--desplegar", str(tmp_path), AGROVERSEX_DATOS=str(tmp_path))
    assert r.returncode != 0 and falta in r.stderr


def test_archivo_vacio_se_rechaza(tmp_path):
    datos_falsos(tmp_path)
    (tmp_path / "teselas/adm0.pmtiles").write_bytes(b"")
    with pytest.raises(c.ErrorDespliegue, match="adm0"):
        c.raiz_datos({"AGROVERSEX_DATOS": str(tmp_path)})


def test_con_todo_presente_raiz_datos_responde(tmp_path):
    assert c.raiz_datos({"AGROVERSEX_DATOS": str(datos_falsos(tmp_path))}) == tmp_path
