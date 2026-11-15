# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Recorrido visual del núcleo del gemelo: entradas, cada paso de la dinámica y el resultado.

Uso (desde la raíz del repositorio):
    .venv/Scripts/python.exe ejemplos/visualizar_gemelo.py
Edite el bloque PARÁMETROS. Cada paso imprime una explicación en la consola y guarda una figura PNG.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

# ===================================================================================================== PARÁMETROS
ESCENARIO = RAIZ / "ejemplos" / "escenario_ames.yaml"   # o escenario_ipiales.yaml, o su propio YAML
ESTRATEGIAS = None              # None = todas; o una lista de ids, p. ej. ["A", "D"]
TIPO_CLIMA = "seco"               # None = el del YAML; o "historico", "seco", "normal", "humedo"
ANIOS = None                    # None = el del YAML; horizonte en años
MAX_MIEMBROS_CLIMA = 8          # miembros climáticos del ensamble
N_PARAMETROS = 6                # muestras LHS de theta (la 0 es la central)
SEMILLA = 42
CALIBRACION = {}                # datos locales, p. ej. {"cn.n_mineral_inicial_kg_ha": 25}
MIEMBRO_CLIMA_DETALLE = 0       # qué miembro climático mostrar día a día (0..MAX_MIEMBROS_CLIMA-1)
N_SUB = 1                       # subpasos por día
OPTIMIZAR = False               # True: también corre NSGA-II (sección `optimizacion` del YAML), ~30-60 s
CARPETA_SALIDA = RAIZ / "salidas" / "visual"
MOSTRAR_VENTANAS = True         # False: solo guarda los PNG
# ================================================================================================================

import matplotlib

if not MOSTRAR_VENTANAS:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from gemelo import indicadores as ind
from gemelo.entrada import leer_entrada
from gemelo.escenarios import construir, series
from gemelo.modelos import fecha_legible
from gemelo.simulador import ejecutar, resumir_estrategias

COLORES = plt.rcParams["axes.prop_cycle"].by_key()["color"]
plt.rcParams.update({"figure.dpi": 100, "axes.grid": True, "grid.alpha": 0.3, "axes.titlesize": 10,
                     "axes.labelsize": 9, "legend.fontsize": 8})


def titulo(paso: int, texto: str) -> None:
    print(f"\n{'=' * 100}\nPASO {paso}. {texto}\n{'=' * 100}")


def guardar(fig, nombre: str) -> None:
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_SALIDA / f"{nombre}.png"
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    print(f"  figura: {ruta.relative_to(RAIZ)}")


def ejes_tiempo(ax, H: int) -> None:
    for a in range(1, H):
        ax.axvline(365 * a, color="k", lw=0.6, alpha=0.4)
    ax.set_xlim(0, 365 * H)
    ax.set_xticks([365 * a + d for a in range(H) for d in (0, 90, 181, 273)])
    ax.set_xticklabels([f"A{a + 1}\n{m}" for a in range(H) for m in ("ene", "abr", "jul", "oct")], fontsize=7)


# ----------------------------------------------------------------------------------------------- 0. preparar
entrada = leer_entrada(ESCENARIO)
if ESTRATEGIAS:
    entrada.estrategias = [e for e in entrada.estrategias if e.id in ESTRATEGIAS]
    if not entrada.estrategias:
        raise SystemExit(f"ninguna estrategia con ids {ESTRATEGIAS}")
if TIPO_CLIMA or ANIOS or MAX_MIEMBROS_CLIMA:
    entrada.escenario = construir(entrada.clima, TIPO_CLIMA or entrada.escenario.tipo,
                                  ANIOS or entrada.escenario.anios_horizonte, SEMILLA,
                                  n_miembros=MAX_MIEMBROS_CLIMA if (TIPO_CLIMA or entrada.escenario.tipo) in
                                  ("seco", "normal", "humedo") else None,
                                  max_miembros=MAX_MIEMBROS_CLIMA)
calibracion = {**entrada.calibracion, **CALIBRACION}
ids = [e.id for e in entrada.estrategias]
ref = entrada.simulacion.get("referencia")
referencia = ids.index(ref) if ref in ids else 0
esc, clima = entrada.escenario, entrada.clima
H = esc.anios_horizonte
k_det = min(MIEMBRO_CLIMA_DETALLE, esc.n_miembros - 1)

# --------------------------------------------------------------------------------------------- 1. clima
titulo(1, "CLIMA e(t): series diarias reales del registro y escenario")
clim, metodo = series(clima, esc)
anios_det = [int(clima.anios[i]) for i in esc.miembros[k_det]]
print(f"  fuente: {clima.fuente} | naturaleza: {clima.naturaleza} | lat {clima.lat:.3f}, {clima.elevacion_m:.0f} m")
print(f"  escenario {esc.tipo}, {esc.n_miembros} miembros de {H} años. Detalle diario: años {anios_det}")
print(f"  ET0 por {metodo}. Lluvia anual media del registro: {clima.precip_anual().mean():.0f} mm")
print(f"  aviso: {esc.aviso}")
t = np.arange(365 * H)
fig, ax = plt.subplots(4, 1, figsize=(13, 9), sharex=True)
ax[0].bar(t, clim["precip"][k_det], width=1, color=COLORES[0])
ax[0].set_ylabel("lluvia mm/día")
ax[0].set_title(f"Clima del miembro {k_det} (años reales {anios_det}) — {clima.fuente}")
ax[1].fill_between(t, clim["t2m_min"][k_det], clim["t2m_max"][k_det], alpha=0.35, color=COLORES[3], label="Tmín-Tmáx")
ax[1].plot(t, clim["t2m"][k_det], color=COLORES[3], lw=0.8, label="Tmedia")
ax[1].set_ylabel("°C")
ax[1].legend(loc="upper right")
ax[2].plot(t, clim["rad_sw"][k_det], color=COLORES[1], lw=0.8)
ax[2].set_ylabel("Rs MJ/m²/día")
ax[3].plot(t, clim["et0"][k_det], color=COLORES[2], lw=0.8)
ax[3].set_ylabel(f"ET0 mm/día\n({metodo})")
ejes_tiempo(ax[3], H)
guardar(fig, "paso1_clima")

fig, ax = plt.subplots(figsize=(11, 3.5))
p_anual = clima.precip_anual()
usados = sorted({i for m in esc.miembros for i in m})
ax.bar(clima.anios, p_anual, color=["C1" if i in usados else "0.75" for i in range(clima.n_anios)])
ax.axhline(np.median(p_anual), color="k", ls="--", lw=0.8, label="mediana")
ax.set_ylabel("lluvia anual mm")
ax.set_title("Registro histórico: años usados por el escenario en color")
ax.legend()
guardar(fig, "paso1_registro_anual")

# --------------------------------------------------------------------------------------------- 2. suelo
titulo(2, "SUELO: propiedades con procedencia (SoilGrids -> Saxton y Rawls)")
suelo = entrada.suelo
for k, p in suelo.parametros.items():
    rango = f"[{p.rango[0]:.3g}, {p.rango[1]:.3g}]" if p.rango else ""
    print(f"  {k:<22} {p.valor:>10.4g} {p.unidad:<14} {p.etiqueta:<11} {rango:<20} {p.naturaleza}")
for a in suelo.avisos:
    print(f"  AVISO: {a}")
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
nombres = ["theta_pmp", "theta_cc", "theta_sat"]
vals = [suelo.valor(n) for n in nombres]
err = [[v - suelo[n].rango[0] for n, v in zip(nombres, vals)], [suelo[n].rango[1] - v for n, v in zip(nombres, vals)]]
ax[0].bar(["marchitez (1500 kPa)", "capacidad de campo (33 kPa)", "saturación"], vals, yerr=err, capsize=5,
          color=[COLORES[3], COLORES[0], COLORES[9 % len(COLORES)]])
ax[0].set_ylabel("m³/m³")
ax[0].set_title("Contenidos de agua (barra = rango del ensamble)")
zp = suelo.valor("profundidad_perfil_m")
ax[1].barh(["agua disponible\n(CC - PMP)"], [1000 * zp * (vals[1] - vals[0])], color=COLORES[0])
ax[1].barh(["agua drenable\n(Sat - CC)"], [1000 * zp * (vals[2] - vals[1])], color=COLORES[1])
ax[1].set_xlabel(f"mm en {zp:.1f} m de perfil")
ax[1].set_title(f"Ksat {suelo.valor('ksat_mm_h'):.1f} mm/h · COS {suelo.valor('cos_t_ha'):.0f} t C/ha · "
                f"MO {suelo.valor('mo_pct'):.1f} %")
guardar(fig, "paso2_suelo")

# --------------------------------------------------------------------------------------------- 3. simular
titulo(3, f"SIMULACIÓN: ensamble {len(ids)} estrategias x {esc.n_miembros} climas x {N_PARAMETROS} muestras de theta")
ens = ejecutar(clima, esc, suelo, entrada.estrategias, n_parametros=N_PARAMETROS, semilla=SEMILLA,
               calibracion=calibracion, n_sub=N_SUB, referencia=referencia,
               equilibrio=entrada.simulacion.get("equilibrio", "completo"))
res = resumir_estrategias(ens, entrada.costos)
reg, prog, ts = ens.reg, ens.prog, ens.theta.ts
K, P, S = ens.K, ens.P, ens.S
print(f"  {S * K * P} miembros simulados día a día durante {365 * H} días")
if ens.carbono_inicial is not None:
    print(f"  equilibrio de carbono con la estrategia de referencia {ens.referencia}: k2 efectivo p50 "
          f"{np.median(ens.carbono_inicial['k2']):.5f}/año (ICBM: {ens.theta.parametros['cn.k2_anual'].valor}/año)")
for a in ens.theta.avisos:
    print(f"  AVISO: {a}")


def miembro(s: int, k: int = k_det, p: int = 0) -> int:
    """Índice del miembro: estrategia s, clima k, parámetros p (p = 0 es theta central)."""
    return (s * K + k) * P + p


# --------------------------------------------------------------------------------------------- 4. manejo
titulo(4, "MANEJO u(t): calendario de temporadas y curva de Kc (FAO-56) de cada estrategia")
fig, ax = plt.subplots(2, 1, figsize=(13, 2 + 1.2 * S), gridspec_kw={"height_ratios": [S, 3]}, sharex=True)
for s, pr in enumerate(ens.programas):
    e = pr.estrategia
    print(f"  {e.id} {e.nombre} [{e.etiqueta}]")
    for tmp, dur in zip(e.temporadas, pr.duraciones):
        ini, n = tmp.siembra, sum(dur)
        print(f"     {tmp.cultivo:<10} siembra {fecha_legible(ini):<16} cosecha {fecha_legible(ini + n - 1):<16} "
              f"etapas {dur} {'cobertura' if not tmp.cosechar else ''} {'riego' if tmp.riego.modo != 'ninguno' else ''}")
        ax[0].barh(s, n, left=ini, color=COLORES[s % len(COLORES)], alpha=0.85 if tmp.cosechar else 0.4,
                   edgecolor="k", hatch=None if tmp.cosechar else "//")
        ax[0].text(ini + n / 2, s, tmp.cultivo, ha="center", va="center", fontsize=7)
    m = miembro(s)
    kc = np.where(prog["cult"][m] >= 0, reg["ETc"][m] / np.maximum(clim["et0"][k_det], 1e-9), np.nan)
    ax[1].plot(t, kc, color=COLORES[s % len(COLORES)], lw=1, label=f"{e.id}")
ax[0].set_yticks(range(S))
ax[0].set_yticklabels([f"{p.estrategia.id} {p.estrategia.nombre[:28]}" for p in ens.programas], fontsize=8)
ax[0].invert_yaxis()
ax[0].set_title("Temporadas (rayado = cultivo de cobertura, no se cosecha)")
ax[1].set_ylabel("Kc efectivo")
ax[1].set_title("Kc = ETc / ET0 (con dosel real; en barbecho no se dibuja)")
ax[1].legend(ncol=S)
ejes_tiempo(ax[1], H)
guardar(fig, "paso4_manejo")

# ------------------------------------------------------------------------------ 5. estado x(t) día a día
titulo(5, "ESTADO x(t) = [W, N, C, B, V] día a día (miembro climático elegido, theta central)")
th_cc, th_pmp, zp_m = ts["th_cc"][0], ts["th_pmp"][0], ts["zp"][0]
fig, ax = plt.subplots(6, 1, figsize=(13, 14), sharex=True)
for s, pr in enumerate(ens.programas):
    m, c = miembro(s), COLORES[s % len(COLORES)]
    lab = pr.estrategia.id
    ax[0].plot(t, reg["W"][m], color=c, lw=0.9, label=lab)
    ax[1].plot(t, reg["agua_raiz"][m], color=c, lw=0.9)
    ax[2].plot(t, reg["N"][m], color=c, lw=0.9)
    ax[3].plot(t, reg["C"][m], color=c, lw=0.9)
    ax[4].plot(t, reg["B"][m], color=c, lw=0.9)
    ax[5].plot(t, reg["V"][m], color=c, lw=1.1)
    ax[5].plot(t, reg["f_residuo"][m], color=c, lw=0.8, ls=":")
    cos = np.where(prog["cosecha"][m])[0]
    ax[4].scatter(cos, reg["b_cosecha"][m, cos], color=c, marker="v", s=25, zorder=3)
ax[0].axhline(1000 * th_cc * zp_m, color="k", ls="--", lw=0.7, label="capacidad de campo")
ax[0].axhline(1000 * th_pmp * zp_m, color="r", ls="--", lw=0.7, label="marchitez")
ax[0].set_ylabel("W agua del perfil mm")
ax[0].legend(ncol=S + 2, loc="upper right")
ax[1].set_ylabel("agua disponible\nzona radicular (0-1)")
ax[2].set_ylabel("N mineral kg N/ha")
ax[3].set_ylabel("C suelo t C/ha")
ax[4].set_ylabel("B biomasa kg MS/ha\n(▼ cosecha)")
ax[5].set_ylabel("V cobertura (—)\nresiduo (···)")
ax[5].set_ylim(0, 1.02)
ejes_tiempo(ax[5], H)
ax[0].set_title(f"Estado del gemelo, clima {anios_det}, theta central")
guardar(fig, "paso5_estado_diario")

# ------------------------------------------------------------------------------- 6. procesos y flujos
titulo(6, "PROCESOS: estrés hídrico Ks, límite de N, flujos de agua y nitrógeno (acumulados)")
fig, ax = plt.subplots(S, 3, figsize=(15, 2.8 * S), squeeze=False)
for s, pr in enumerate(ens.programas):
    m = miembro(s)
    act = prog["cult"][m] >= 0
    ax[s, 0].plot(t, np.where(act, reg["K"][m], np.nan), color=COLORES[0], lw=0.8, label="Ks (agua)")
    ax[s, 0].plot(t, np.where(act, reg["ETa"][m] / np.maximum(reg["ETc"][m], 1e-9), np.nan), color=COLORES[1],
                  lw=0.6, alpha=0.7, label="ETa/ETc")
    ax[s, 0].set_ylim(0, 1.05)
    ax[s, 0].set_ylabel(f"{pr.estrategia.id}")
    for nombre, clave, col in (("lluvia", "P", 0), ("riego", "I_bruto", 9), ("ET real", "ETa", 2),
                               ("escorrentía", "R", 3), ("drenaje", "D", 4)):
        ax[s, 1].plot(t, np.cumsum(reg[clave][m]), color=COLORES[col % len(COLORES)], lw=1, label=nombre)
    for nombre, clave, col in (("fertilizante al suelo", "fert_suelo", 0), ("fijación", "fijacion", 2),
                               ("absorción del suelo", "U", 1), ("lixiviación", "L_lix", 3),
                               ("volatilización", "L_vol", 4), ("exportado en cosecha", "N_export", 5),
                               ("mineralización neta", "M_neta", 6)):
        ax[s, 2].plot(t, np.cumsum(reg[clave][m]), color=COLORES[col % len(COLORES)], lw=1, label=nombre)
    for a in ax[s]:
        ejes_tiempo(a, H)
    m_txt = (f"  {pr.estrategia.id}: lluvia {reg['P'][m].sum():.0f} mm, ETa {reg['ETa'][m].sum():.0f}, "
             f"drenaje {reg['D'][m].sum():.0f}, escorrentía {reg['R'][m].sum():.0f}, riego {reg['I_bruto'][m].sum():.0f}"
             f" | N: fert {reg['fert_suelo'][m].sum():.0f}, fijado {reg['fijacion'][m].sum():.0f}, "
             f"lixiviado {reg['L_lix'][m].sum():.0f}, exportado {reg['N_export'][m].sum():.0f} kg/ha")
    print(m_txt)
ax[0, 0].set_title("Estrés: Ks y ETa/ETc en días de cultivo")
ax[0, 1].set_title("Agua acumulada, mm")
ax[0, 2].set_title("Nitrógeno acumulado, kg N/ha")
ax[0, 0].legend(loc="lower left")
ax[0, 1].legend(loc="upper left")
ax[0, 2].legend(loc="upper left", fontsize=6)
guardar(fig, "paso6_procesos")

# ------------------------------------------------------------------------------------ 7. balances de masa
titulo(7, "CONSERVACIÓN: el agua, el N y el C cierran (error numérico por miembro)")
ini = reg["inicial"]
w_prev = np.concatenate([ini["W"][:, None], reg["W"][:, :-1]], axis=1)
err_w = np.abs(reg["W"] - w_prev - (reg["P"] + reg["I_neto"] - reg["ETa"] - reg["R"] - reg["D"])).max(1)
err_c = np.abs(reg["C"][:, -1] - ini["C"] - (reg["c_entrada"].sum(1) - reg["resp"].sum(1)))
cn = np.tile(ts["cn_suelo"], S * K)
n_tot0 = ini["N"] + ini["Y_N"] + ini["O"] * 1000 / cn
n_tot1 = reg["N"][:, -1] + reg["Y_N"][:, -1] + reg["O"][:, -1] * 1000 / cn + reg["N_planta"][:, -1]
err_n = np.abs(n_tot1 - n_tot0 - (reg["fert_suelo"].sum(1) + reg["fijacion"].sum(1) - reg["L_lix"].sum(1)
                                  - reg["N_export"].sum(1)))
print(f"  máximo error en todos los miembros: agua {err_w.max():.2e} mm | C {err_c.max():.2e} t/ha | "
      f"N {err_n.max():.2e} kg/ha")
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
for s, pr in enumerate(ens.programas):
    b = ens.bloque(s)
    entra = [np.median(reg["fert_suelo"][b].sum(1) / H), np.median(reg["fijacion"][b].sum(1) / H)]
    sale = [np.median(reg["L_lix"][b].sum(1) / H), np.median(reg["N_export"][b].sum(1) / H),
            np.median(reg["L_vol"][b].sum(1) / H)]
    ax[0].bar(s - 0.2, entra[0], 0.4, color=COLORES[0], label="fertilizante" if s == 0 else None)
    ax[0].bar(s - 0.2, entra[1], 0.4, bottom=entra[0], color=COLORES[2], label="fijación" if s == 0 else None)
    ax[0].bar(s + 0.2, -sale[0], 0.4, color=COLORES[3], label="lixiviación" if s == 0 else None)
    ax[0].bar(s + 0.2, -sale[1], 0.4, bottom=-sale[0], color=COLORES[5], label="exportación" if s == 0 else None)
    ax[0].bar(s + 0.2, -sale[2], 0.4, bottom=-sale[0] - sale[1], color=COLORES[4],
              label="volatilización" if s == 0 else None)
    ent_c, resp = np.median(reg["c_entrada"][b].sum(1) / H), np.median(reg["resp"][b].sum(1) / H)
    ax[1].bar(s - 0.2, ent_c, 0.4, color=COLORES[2], label="entrada de residuo" if s == 0 else None)
    ax[1].bar(s + 0.2, -resp, 0.4, color=COLORES[3], label="respiración" if s == 0 else None)
    ax[1].scatter(s, ent_c - resp, color="k", zorder=3, label="cambio neto" if s == 0 else None)
ax[0].axhline(0, color="k", lw=0.7)
ax[0].set_title("Balance de N p50, kg N/ha/año (+ entra, − sale)")
ax[1].axhline(0, color="k", lw=0.7)
ax[1].set_title("Balance de C p50, t C/ha/año")
for a in ax[:2]:
    a.set_xticks(range(S))
    a.set_xticklabels(ids)
    a.legend(fontsize=7)
ax[2].semilogy(np.maximum(err_w, 1e-17), ".", label="agua (mm)")
ax[2].semilogy(np.maximum(err_c, 1e-17), ".", label="C (t/ha)")
ax[2].semilogy(np.maximum(err_n, 1e-17), ".", label="N (kg/ha)")
ax[2].set_xlabel("miembro del ensamble")
ax[2].set_title("Error de cierre de masa (redondeo de máquina)")
ax[2].legend()
guardar(fig, "paso7_balances")

# ----------------------------------------------------------------------------- 8. incertidumbre mensual
titulo(8, "INCERTIDUMBRE: trayectorias mensuales p10-p50-p90 sobre clima x parámetros")
variables = [("W", "agua del perfil mm"), ("N", "N mineral kg/ha"), ("C", "C suelo t C/ha"),
             ("B", "biomasa kg MS/ha"), ("V", "cobertura"), ("L_lix", "lixiviación mensual kg N/ha")]
fig, ax = plt.subplots(len(variables), 1, figsize=(13, 2.3 * len(variables)), sharex=True)
meses = np.arange(12 * H) + 0.5
for s, e in enumerate(res):
    c = COLORES[s % len(COLORES)]
    for a, (v, etiqueta) in zip(ax, variables):
        q = e["trayectoria_mensual"][v]
        a.fill_between(meses, q["p10"], q["p90"], color=c, alpha=0.18)
        a.plot(meses, q["p50"], color=c, lw=1.3, label=e["id"] if v == "W" else None)
        a.set_ylabel(etiqueta)
ax[0].legend(ncol=S)
ax[0].set_title("Banda = p10-p90; línea = p50")
ax[-1].set_xticks(np.arange(0, 12 * H + 1, 3))
ax[-1].set_xticklabels([f"A{m // 12 + 1}-{m % 12 + 1:02d}" for m in range(0, 12 * H + 1, 3)], fontsize=7)
ax[-1].set_xlabel("mes")
guardar(fig, "paso8_incertidumbre")

# ------------------------------------------------------------------------------------------- 9. resultado
titulo(9, "RESULTADO: indicadores por estrategia (p50 con rango p10-p90)")
claves = ["produccion_relativa_anio", "rendimiento_relativo", "deficit_relativo", "riego_mm_anio",
          "lixiviacion_n_kg_ha_anio", "fijacion_n_kg_ha_anio", "cambio_carbono_t_ha_anio",
          "lluvia_intensa_sobre_suelo_desnudo_mm_anio", "cobertura_media"]
print(f"  {'indicador':<30}" + "".join(f"{e['id']:>24}" for e in res))
for k in claves:
    fila = [e["indicadores"][k] for e in res]
    print(f"  {k:<30}" + "".join(f"{f['p50']:>10.3g} [{f['p10']:.3g}, {f['p90']:.3g}]".rjust(24) for f in fila))
fig, ax = plt.subplots(3, 3, figsize=(15, 10))
for a, k in zip(ax.flat, claves):
    p50 = np.array([e["indicadores"][k]["p50"] for e in res])
    lo = p50 - np.array([e["indicadores"][k]["p10"] for e in res])
    hi = np.array([e["indicadores"][k]["p90"] for e in res]) - p50
    a.bar(ids, p50, yerr=[lo, hi], capsize=4, color=[COLORES[i % len(COLORES)] for i in range(S)])
    a.axhline(0, color="k", lw=0.6)
    a.set_title(f"{k}\n({ind.DEFINICIONES[k][0]})", fontsize=9)
fig.suptitle("Indicadores del horizonte: barra = p50, línea = p10-p90", y=1.0)
guardar(fig, "paso9_resultado")

fig, ax = plt.subplots(1, 2, figsize=(15, 4.5))
x = 0
etiquetas = []
for s, e in enumerate(res):
    for tmp in e["temporadas"]:
        it = tmp["indicadores"]
        y = it["biomasa_kg_ha"]["p50"] if not tmp["cosechar"] else it["rendimiento_kg_ha"]["p50"]
        ax[0].bar(x, y, color=COLORES[s % len(COLORES)], alpha=1 if tmp["cosechar"] else 0.4,
                  yerr=[[y - (it["rendimiento_kg_ha"] if tmp["cosechar"] else it["biomasa_kg_ha"])["p10"]],
                        [(it["rendimiento_kg_ha"] if tmp["cosechar"] else it["biomasa_kg_ha"])["p90"] - y]],
                  capsize=3)
        ax[1].scatter(x, it["rendimiento_relativo"]["p50"], color=COLORES[s % len(COLORES)], marker="o")
        ax[1].scatter(x, it["aptitud_termica"]["p50"], color=COLORES[s % len(COLORES)], marker="^")
        etiquetas.append(f"{e['id']}\n{tmp['cultivo']}\n{tmp['siembra']}")
        x += 1
for a in ax:
    a.set_xticks(range(x))
    a.set_xticklabels(etiquetas, fontsize=6)
ax[0].set_title("Rendimiento cosechado por temporada, kg MS/ha (claro = biomasa de cobertura)")
ax[1].set_title("● rendimiento relativo Y/Ypot (agua y N)   ▲ aptitud térmica Ypot/Ymax (temperatura)")
ax[1].set_ylim(0, 1.05)
guardar(fig, "paso9_temporadas")

print("\n  AVISOS PARA EL USUARIO:")
for a in dict.fromkeys([esc.aviso, *ens.theta.avisos]):
    print(f"   - {a}")

# ------------------------------------------------------------------------------------- 10. optimización
if OPTIMIZAR:
    from gemelo.api import optimizar_rotacion
    titulo(10, "OPTIMIZACIÓN NSGA-II: frente de compromisos frente a la línea base")
    doc = optimizar_rotacion(ESCENARIO)
    objs = [o["id"] for o in doc["objetivos"]]
    base = doc["linea_base"]["objetivos"]
    frente = doc["frente"]
    for f in frente:
        print(f"  {f['id']} {f['secuencia']}")
        print(f"      gana: {f['frente_a_linea_base']['gana']}")
        print(f"      cede: {f['frente_a_linea_base']['cede']}")
    for linea in doc["compromisos"]["explicacion"]:
        print(f"  {linea}")
    pares = [(objs[i], objs[j]) for i in range(len(objs)) for j in range(i + 1, len(objs))][:6]
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    comp = doc["compromisos"]["compromiso_equilibrado"]
    for a, (ox, oy) in zip(ax.flat, pares):
        a.scatter([f["objetivos"][ox] for f in frente], [f["objetivos"][oy] for f in frente], color=COLORES[0],
                  label="candidatas")
        for f in frente:
            a.annotate(f["id"], (f["objetivos"][ox], f["objetivos"][oy]), fontsize=7,
                       fontweight="bold" if f["id"] == comp else None)
        a.scatter(base[ox], base[oy], color="r", marker="*", s=150, label="línea base")
        a.set_xlabel(f"{ox} ({'más es mejor' if doc['objetivos'][objs.index(ox)]['sentido'] == 'max' else 'menos es mejor'})")
        a.set_ylabel(oy)
    ax.flat[0].legend()
    fig.suptitle(f"Frente NSGA-II (compromiso equilibrado: {comp})")
    guardar(fig, "paso10_optimizacion")

print(f"\nListo. Figuras en {CARPETA_SALIDA.relative_to(RAIZ)}")
if MOSTRAR_VENTANAS:
    plt.show()
