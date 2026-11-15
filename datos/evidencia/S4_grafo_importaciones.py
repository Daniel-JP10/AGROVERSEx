# asistido por SI: Claude Code (Anthropic), grafo estatico de importaciones para la decision i
# Reproduce: C:\NASA\AGROVERSEx\.venv\Scripts\python.exe datos/evidencia/S4_grafo_importaciones.py [raiz_del_worktree]
# Salida: datos/evidencia/S4_grafo_importaciones.txt
import ast, os, re, sys

RAIZ = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(RAIZ, "src")
GENERADOR = "simulacion"
# candidatos del generador simulado = todo src/simulacion fuera de geo/
SALTAR = {"node_modules", ".git", "dist", "__pycache__", ".venv"}


def py_files(base):
    for d, ds, fs in os.walk(base):
        ds[:] = [x for x in ds if x not in SALTAR]
        for f in fs:
            if f.endswith(".py"):
                yield os.path.join(d, f)


def nombre_modulo(ruta):
    # nombre con puntos relativo a src; fuera de src, relativo a la raiz del repo
    rel = os.path.relpath(ruta, SRC if ruta.startswith(SRC) else RAIZ)[:-3].replace(os.sep, ".")
    return rel[:-9] if rel.endswith(".__init__") else rel


def importaciones(ruta, mod):
    # devuelve (lista de nombres absolutos importados, lista de llamadas dinamicas)
    arbol = ast.parse(open(ruta, "rb").read(), ruta)
    es_paquete = os.path.basename(ruta) == "__init__.py"
    pkg = mod if es_paquete else mod.rpartition(".")[0]
    out, dyn = [], []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            out += [(a.name, None) for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg.split(".")
                base = base[: len(base) - (n.level - 1)]
                b = ".".join(base + ([n.module] if n.module else []))
            else:
                b = n.module
            out += [(b, a.name) for a in n.names]
        elif isinstance(n, ast.Call):
            f = n.func
            nom = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nom in ("__import__", "import_module", "reload", "run_module", "run_path", "exec", "eval"):
                dyn.append((n.lineno, nom))
    return out, dyn


def main():
    todos = {}
    for base in (SRC, os.path.join(RAIZ, "pruebas"), os.path.join(RAIZ, "datos"), os.path.join(RAIZ, "ejemplos"), os.path.join(RAIZ, "herramientas")):
        for p in py_files(base):
            todos[nombre_modulo(p)] = p
    # modulos del generador: .py directos de src/simulacion
    gen = sorted(m for m in todos if m.startswith(GENERADOR + ".") and not m.startswith(GENERADOR + ".geo") and m not in (GENERADOR + ".referencias",))
    geo = sorted(m for m in todos if m.startswith(GENERADOR + ".geo"))
    existentes = set(todos)

    def resolver(base, nombre):
        # lleva "base" + "nombre" importado a un modulo conocido
        if nombre and f"{base}.{nombre}" in existentes:
            return f"{base}.{nombre}"
        return base if base in existentes else None

    quien = {g: set() for g in gen}
    dinamicas = []
    for mod, ruta in todos.items():
        imps, dyn = importaciones(ruta, mod)
        for lin, nom in dyn:
            dinamicas.append((os.path.relpath(ruta, RAIZ), lin, nom))
        for base, nombre in imps:
            if not base:
                continue
            destino = resolver(base, nombre)
            if destino in quien and destino != mod:
                quien[destino].add(mod)
            # "from simulacion import x" ya cubierto por resolver; "import simulacion" no trae submodulos
    # texto: referencias fuera de Python (ts, tsx, json, yaml, sh, md) a src/simulacion
    textos = []
    for d, ds, fs in os.walk(RAIZ):
        ds[:] = [x for x in ds if x not in SALTAR]
        for f in fs:
            if f.endswith((".py", ".ts", ".tsx", ".mjs", ".js", ".json", ".yaml", ".yml", ".sh", ".toml", ".cfg", ".ini", ".sql")) and f != "package-lock.json":
                p = os.path.join(d, f)
                try:
                    t = open(p, encoding="utf-8").read()
                except UnicodeDecodeError:
                    continue
                for i, ln in enumerate(t.splitlines(), 1):
                    if re.search(r"src[/\\]simulacion|-m simulacion|simulacion[./\\](clima|vegetacion|agua|cobertura|suelo|lotes|escribir_sqlite|variables|tiempo|config|azar|condicion|incertidumbre|productos|rotaciones|referencias)|esquema_agroversex|zonas_agroversex|agroversex_muestra|escribir_sqlite|geo\.sqlite", ln):
                        textos.append((os.path.relpath(p, RAIZ), i, ln.strip()[:160]))

    def grupo(m):
        if m.startswith("pruebas.sim"): return "pruebas/sim (del generador)"
        if m.startswith("pruebas."): return "pruebas que se quedan"
        if m.startswith("simulacion.geo"): return "SE QUEDA: pipeline geo"
        if m.startswith("simulacion."): return "generador"
        return "SE QUEDA: " + m.split(".")[0]

    lineas = [f"Raiz: {RAIZ}", f"Modulos Python analizados: {len(todos)}", ""]
    lineas.append("Importadores por modulo del generador (src/simulacion/*.py)")
    for g in gen:
        imp = sorted(quien[g])
        quedan = [m for m in imp if grupo(m).startswith("SE QUEDA")]
        entre = [m for m in imp if grupo(m) == "generador"]
        tests_sim = [m for m in imp if grupo(m) == "pruebas/sim (del generador)"]
        otros = [m for m in imp if grupo(m) == "pruebas que se quedan"]
        lineas.append(f"- {g}: de los que se quedan: {quedan or 'nadie'}; de pruebas que se quedan: {otros or 'nadie'}; "
                      f"del generador: {entre or 'nadie'}; de pruebas/sim: {len(tests_sim)}")
    lineas += ["", "Archivos de pruebas/sim: modulos del generador y de geo que importan (los que dependen solo del generador salen con el)"]
    for m, ruta in sorted(todos.items()):
        if m.startswith("pruebas.sim"):
            ig = sorted({(destino or "").split(".", 1)[1] for b, n in importaciones(ruta, m)[0] if b for destino in [resolver(b, n)] if destino and destino.startswith("simulacion.")})
            lineas.append(f"- {os.path.relpath(ruta, RAIZ)}: {ig}")
    lineas += ["", "Llamadas dinamicas (__import__, import_module, reload, run_module, exec, eval) en Python:"]
    lineas += [f"- {a}:{b} {c}" for a, b, c in dinamicas] or ["- ninguna"]
    lineas += ["", "Referencias de texto fuera de Python a simulacion o a artefactos del generador (ts, tsx, json, yaml, sh):"]
    lineas += [f"- {a}:{b} {c}" for a, b, c in textos] or ["- ninguna"]
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "S4_grafo_importaciones.txt")
    open(salida, "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("\n".join(lineas))


main()
