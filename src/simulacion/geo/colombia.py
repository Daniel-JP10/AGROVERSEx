# asistido por SI: Claude Code (Anthropic), comparación de municipios de CGAZ contra DIVIPOLA del DANE (T-D1)
import re
from difflib import SequenceMatcher, get_close_matches

import pandas as pd

from simulacion.geo.normalizar import normalizar_nombre

# parecido mínimo para dar por buena una variante de nombre dentro del mismo departamento
UMBRAL = 0.6


def _clave(s: str) -> str:
    # sin paréntesis (CGAZ añade la cabecera municipal), sin puntuación y sin tildes
    s = re.sub(r"\(.*?\)", " ", str(s))
    return re.sub(r"[^a-z0-9]+", " ", normalizar_nombre(s)).strip()


def _parecido(a: str, b: str):
    # una clave contenida en la otra por palabras completas (Cali en Santiago de Cali) vale como variante
    pa, pb = set(a.split()), set(b.split())
    if pa and pb and (pa <= pb or pb <= pa):
        return 0.9, "contiene"
    return SequenceMatcher(None, a, b).ratio(), "parecido"


def _variante(c, d, dep, r, metodo):
    return {"cgaz": c["nombre"], "dane": d["nom_mpio"], "dpto": dep, "parecido": round(r, 2),
            "cod_mpio": d["cod_mpio"], "metodo": metodo}


def padre_de(u: pd.DataFrame, nombre: str) -> str | None:
    fila = u[u["nombre"] == nombre].iloc[0]
    padre = u[u["unidad_id"] == fila["padre_id"]]
    return None if padre.empty else padre.iloc[0]["nombre"]


def comparar_divipola(cgaz: pd.DataFrame, dane: pd.DataFrame) -> dict:
    """cgaz: unidad_id, nombre, dpto (nombre del departamento). dane: cod_mpio, nom_mpio, dpto, tipo_municipio.
    Empareja por departamento y nombre; lo no exacto se empareja por parecido dentro del departamento."""
    c, d = cgaz.copy(), dane.copy()
    c["k"], d["k"] = c["nombre"].map(_clave), d["nom_mpio"].map(_clave)
    deps_d = d["dpto"].map(_clave).unique().tolist()
    # el departamento de CGAZ se lleva al de DIVIPOLA por parecido (Bogotá se llama distinto)
    mapa = {x: (get_close_matches(x, deps_d, n=1, cutoff=0.4) or [None])[0] for x in c["dpto"].map(_clave).unique()}
    c["dep"], d["dep"] = c["dpto"].map(_clave).map(mapa), d["dpto"].map(_clave)
    exactos, variantes, candidatos, sobran, faltan = 0, [], [], [], []
    for dep in sorted(set(c["dep"].dropna()) | set(d["dep"])):
        cc, dd = c[c["dep"] == dep], d[d["dep"] == dep]
        ex = set(cc["k"]) & set(dd["k"])
        exactos += len(ex)
        cc, dd = cc[~cc["k"].isin(ex)], dd[~dd["k"].isin(ex)]
        pares = sorted(((_parecido(a.k, b.k), i, j) for i, a in cc.iterrows() for j, b in dd.iterrows()),
                       key=lambda x: -x[0][0])
        usados_c, usados_d = set(), set()
        for (r, metodo), i, j in pares:
            if r >= UMBRAL and i not in usados_c and j not in usados_d:
                usados_c.add(i)
                usados_d.add(j)
                variantes.append(_variante(cc.loc[i], dd.loc[j], dep, r, metodo))
        resto_c, resto_d = cc[~cc.index.isin(usados_c)], dd[~dd.index.isin(usados_d)]
        if len(resto_c) == 1 and len(resto_d) == 1:  # único resto del departamento: candidato, no confirmado
            candidatos.append(_variante(resto_c.iloc[0], resto_d.iloc[0], dep, 0.0, "exclusion"))
        sobran += cc.loc[~cc.index.isin(usados_c), "nombre"].tolist()
        faltan += dd.loc[~dd.index.isin(usados_d), "nom_mpio"].tolist()
    return {"cgaz": len(c), "dane": len(d), "exactos": exactos, "variantes": variantes, "candidatos_por_exclusion": candidatos,
            "sobran_en_cgaz": sobran, "faltan_en_cgaz": faltan}
