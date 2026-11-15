# asistido por SI: Claude Code (Anthropic), RED de test_registros.py con la copia de filas sueltas
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(raiz / "pruebas"))
from test_registros import filas_sueltas
for ruta in [raiz / "datos/evidencia/S4_registros_con_filas_sueltas.md", raiz / "SI_USO.md"]:
    e = filas_sueltas(ruta.read_text(encoding="utf-8"))
    print(ruta.name, "->", len(e), "filas sueltas", e)
