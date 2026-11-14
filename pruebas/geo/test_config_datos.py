# asistido por SI: Claude Code (Anthropic), prueba de la variable AGRO_DATOS (T-D1)
import importlib

import simulacion.config as cfg


def test_agro_datos_redirige_crudos_y_procesados(monkeypatch, tmp_path):
    monkeypatch.setenv("AGRO_DATOS", str(tmp_path))
    try:
        c = importlib.reload(cfg)
        assert c.CRUDOS == tmp_path / "crudos" and c.PROCESADOS == tmp_path / "procesados"
    finally:
        monkeypatch.delenv("AGRO_DATOS")
        c = importlib.reload(cfg)
    assert c.CRUDOS == c.RAIZ / "datos/crudos"
