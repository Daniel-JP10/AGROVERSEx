# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Dinámica del gemelo dx/dt = f(x, u, e, theta), integrada a paso diario y vectorizada sobre M miembros.

x = [W, N, C, B, V] (más subestados internos: W1/W2, Y/O/Y_N, N de la planta, residuo superficial).
Método: Euler explícito con división de operadores y flujos limitados (ningún flujo saca más de lo que hay), lo
que garantiza no negatividad y cierre exacto de masa de agua, N y C. `n_sub` > 1 divide los procesos continuos
del día en subpasos para el estudio de convergencia; eventos (siembra, cosecha, riego, escorrentía) son diarios.

Orden dentro del día:
 1. profundidad radicular y redistribución entre capas; eventos de siembra y labranza
 2. riego automático (agotamiento al inicio del día) y escorrentía por número de curva
 3. por subpaso: infiltración, drenaje, ET, cobertura, crecimiento con límite de N, ICBM, lixiviación
 4. cosecha al final del último día de la temporada
"""
from dataclasses import dataclass

import numpy as np

from gemelo import agua, biomasa, carbono, cobertura, nitrogeno
from gemelo.fenologia import cobertura_potencial
from gemelo.suelo import escorrentia_scs, numero_curva_efectivo

# Claves de theta por miembro (M,) y por miembro y cultivo (M, C)
THETA_SUELO = ("zp", "th_cc", "th_pmp", "th_sat", "tau", "cn_cultivo", "cn_desnudo", "cn_residuo_cubierta", "rew",
               "ze", "kc_min", "kc_max_suelo", "red_mulch", "am", "ajuste_p", "zr_ini", "k1", "k2", "h", "t_min_dec",
               "t_ref_dec", "t_norm_dec", "cn_suelo", "fc_residuo", "frac_vol", "efic_riego", "ndfa_max")
THETA_CULTIVO = ("kc_ini", "kc_mid", "kc_end", "zr_max", "p", "altura_m", "rue", "t_base", "t_opt", "t_max",
                 "indice_cosecha", "n_biomasa", "indice_cosecha_n", "ndfa")
REGISTROS = ("W", "W1", "agua_raiz", "N", "C", "B", "V", "f_residuo", "desnudo", "P", "R", "D", "I_bruto", "I_neto",
             "ETa", "ETc", "K", "L_lix", "L_vol", "U", "fijacion", "fert_suelo", "M_neta", "resp", "c_entrada",
             "rend", "rend_pot", "rend_max", "b_cosecha", "z1", "N_export", "N_planta", "Y_N", "O", "r_desc",
             "n_entrada", "res_sup")


@dataclass
class Estado0:
    """Estado inicial por miembro (M,). y0/yn0 explícitos (equilibrio) tienen prioridad sobre frac_joven."""
    frac_agua: np.ndarray       # fracción del agua disponible en todo el perfil
    n_mineral: np.ndarray       # kg N/ha
    cos: np.ndarray             # t C/ha
    frac_joven: np.ndarray
    y0: np.ndarray | None = None
    yn0: np.ndarray | None = None
    res0: np.ndarray | None = None   # kg MS/ha de residuo en superficie al inicio (parte de y0)

    def carbono(self, cn_suelo):
        if self.y0 is None:
            return carbono.inicializar(self.cos, self.frac_joven, cn_suelo)
        return self.y0, self.cos - self.y0, self.yn0


def _tomar(arr_mc, idx):
    """arr (M, C)[m, idx[m]] con idx = -1 en barbecho (devuelve 0)."""
    i = np.maximum(idx, 0)
    return np.where(idx >= 0, np.take_along_axis(arr_mc, i[:, None], axis=1)[:, 0], 0.0)


def preparar_cultivo(prog: dict, tc: dict, ts: dict, t2m: np.ndarray) -> dict:
    """Series (M, T) que dependen del calendario y de los parámetros, no del estado: Kc, Vpot, Zr, f_T."""
    cult = prog["cult"]
    activo = cult >= 0
    i = np.maximum(cult, 0)

    def mt(k):
        return np.take_along_axis(tc[k], i, axis=1)
    kc = prog["w_ini"] * mt("kc_ini") + prog["w_mid"] * mt("kc_mid") + prog["w_end"] * mt("kc_end")
    kc_max = np.maximum(1.20, mt("kc_mid") + 0.05)          # FAO-56 ec. 72 en clima estándar
    vpot = np.where(activo, cobertura_potencial(kc, ts["kc_min"][:, None], kc_max, mt("altura_m")), 0.0)
    zr_cult = ts["zr_ini"][:, None] + (mt("zr_max") - ts["zr_ini"][:, None]) * prog["f_raiz"]
    z1 = np.where(activo, np.maximum(zr_cult, ts["ze"][:, None]), ts["ze"][:, None])
    z1 = np.minimum(z1, 0.95 * ts["zp"][:, None])
    f_t = np.where(activo, biomasa.f_temperatura(t2m, mt("t_base"), mt("t_opt"), mt("t_max")), 0.0)
    return {"kc": np.where(activo, kc, 0.0), "vpot": vpot, "z1": z1, "f_t": f_t,
            "p": np.where(activo, mt("p"), 0.0)}


def simular(clima: dict, prog: dict, ts: dict, tc: dict, x0: Estado0, n_sub: int = 1) -> dict:
    """Integra el gemelo. clima: precip, t2m, rad_sw, et0 en (M, T). Devuelve registros diarios (M, T)."""
    precip, t2m, rs, et0 = (np.asarray(clima[k], float) for k in ("precip", "t2m", "rad_sw", "et0"))
    M, T = precip.shape
    pc = preparar_cultivo(prog, tc, ts, t2m)
    zp = ts["zp"]
    th_cc, th_pmp, th_sat = ts["th_cc"], ts["th_pmp"], ts["th_sat"]
    cn = {"cultivo": ts["cn_cultivo"], "desnudo": ts["cn_desnudo"], "residuo": ts["cn_residuo_cubierta"]}
    tau = agua.tau_subpaso(ts["tau"], n_sub)
    k1d, k2d = ts["k1"] / 365.0, ts["k2"] / 365.0

    # Estado inicial
    z1 = pc["z1"][:, 0].copy()
    w_pmp_tot, w_cc_tot = agua.almacenamiento(th_pmp, zp), agua.almacenamiento(th_cc, zp)
    w_tot = w_pmp_tot + x0.frac_agua * (w_cc_tot - w_pmp_tot)
    w1, w2 = w_tot * z1 / zp, w_tot * (zp - z1) / zp
    n_min = x0.n_mineral.astype(float).copy()
    y, o, y_n = x0.carbono(ts["cn_suelo"])
    inicial = {"W": w_tot, "N": x0.n_mineral.astype(float), "C": (y + o).astype(float), "Y": np.array(y, float),
               "O": np.array(o, float), "Y_N": np.array(y_n, float)}
    b = np.zeros(M)
    b_pot = np.zeros(M)            # sin estrés hídrico ni de N (con límite de temperatura)
    b_max = np.zeros(M)            # solo limitado por radiación: referencia de aptitud térmica
    n_planta = np.zeros(M)
    v = np.zeros(M)
    vpot_ayer = np.zeros(M)
    f_n_ayer = np.ones(M)
    # kg MS/ha de residuo en superficie: subconjunto del reservorio joven, nunca más C que el que tiene Y
    res_sup = np.zeros(M) if x0.res0 is None else np.minimum(x0.res0, y * 1000.0 / ts["fc_residuo"])
    riego_usado = np.zeros(M)

    reg = {k: np.zeros((M, T)) for k in REGISTROS}
    for t in range(T):
        cult = prog["cult"][:, t]
        activo = cult >= 0

        # 1. Raíces y eventos de siembra
        z1_nuevo = pc["z1"][:, t]
        w1, w2 = agua.redistribuir(w1, w2, z1, z1_nuevo, zp)
        z1 = z1_nuevo
        sem = prog["siembra"][:, t]
        b = np.where(sem, 0.0, b)
        b_pot = np.where(sem, 0.0, b_pot)
        b_max = np.where(sem, 0.0, b_max)
        n_planta = np.where(sem, 0.0, n_planta)
        v = np.where(sem, 0.0, v)
        vpot_ayer = np.where(sem, 0.0, vpot_ayer)
        f_n_ayer = np.where(sem, 1.0, f_n_ayer)
        riego_usado = np.where(sem, 0.0, riego_usado)
        res_sup = np.where(prog["labranza"][:, t], 0.0, res_sup)

        w1_cc, w1_pmp, w1_sat = (agua.almacenamiento(th, z1) for th in (th_cc, th_pmp, th_sat))
        w2_cc, w2_sat = agua.almacenamiento(th_cc, zp - z1), agua.almacenamiento(th_sat, zp - z1)
        # En barbecho la capa evaporante puede secarse hasta 0,5 theta_pmp (FAO-56 ec. 73)
        w1_min = np.where(activo, w1_pmp, 0.5 * w1_pmp)
        f_res = cobertura.cobertura_residuo(res_sup, ts["am"])

        # ET potencial del día
        vpot = pc["vpot"][:, t]
        kc_cult = cobertura.kc_efectivo(pc["kc"][:, t], v, vpot, ts["kc_min"])
        kc = np.where(activo, kc_cult, cobertura.kc_suelo_desnudo(ts["kc_max_suelo"], f_res, ts["red_mulch"]))
        etc = kc * et0[:, t]
        p = agua.p_ajustado(pc["p"][:, t], etc, ts["ajuste_p"])
        umbral_mm = np.where(activo, p * (w1_cc - w1_min), ts["rew"])

        # 2. Riego y escorrentía
        i_neto, i_bruto = agua.riego_automatico(activo & prog["riego_auto"][:, t], w1, w1_cc, p * (w1_cc - w1_min),
                                                prog["riego_umbral"][:, t], riego_usado, prog["riego_tope"][:, t],
                                                ts["efic_riego"])
        riego_usado += i_bruto
        cn_ef = numero_curva_efectivo(cn, v, f_res)
        r = escorrentia_scs(precip[:, t], cn_ef)
        fert_in, vol = nitrogeno.fertilizar(prog["fert"][:, t], ts["frac_vol"])
        n_min = n_min + fert_in
        entrada = (precip[:, t] - r + i_neto) / n_sub

        acum = {k: np.zeros(M) for k in ("D", "ETa", "K", "L", "U", "fx", "M", "resp", "Rsat", "r")}
        f_t_dec_base = carbono.factor_temperatura(t2m[:, t], ts["t_min_dec"], ts["t_ref_dec"]) / \
            carbono.factor_temperatura(ts["t_norm_dec"], ts["t_min_dec"], ts["t_ref_dec"])
        for s in range(n_sub):
            # 3a. Agua. El exceso de saturación de la capa 2 al recibir drenaje sale como drenaje profundo.
            w1, w2, exc = agua.infiltrar(w1, w2, entrada, w1_sat, w2_sat)
            d1 = agua.drenaje(w1, w1_cc, tau)
            w1, w2 = w1 - d1, w2 + d1
            rebalse = np.maximum(w2 - w2_sat, 0.0)
            w2 = w2 - rebalse
            d2 = agua.drenaje(w2, w2_cc, tau)
            w2 = w2 - d2
            d2 = d2 + rebalse
            k = agua.coef_estres(w1, w1_cc, w1_min, umbral_mm)
            eta = agua.evapotranspiracion(w1, w1_min, etc / n_sub, k)
            w1 = w1 - eta
            # 3b. Cobertura y biomasa (la expansión potencial del día se reparte entre subpasos)
            g_v = np.minimum(k, f_n_ayer)
            vp_ant = vpot_ayer + (vpot - vpot_ayer) * s / n_sub
            vp_s = vpot_ayer + (vpot - vpot_ayer) * (s + 1) / n_sub
            v = np.where(activo, cobertura.actualizar_cobertura(v, vp_s, vp_ant, g_v), 0.0)
            ks_planta = np.where(activo, k, 0.0)
            db_w = biomasa.crecimiento(_tomar(tc["rue"], cult), v, rs[:, t], pc["f_t"][:, t], ks_planta) / n_sub
            db_pot = biomasa.crecimiento(_tomar(tc["rue"], cult), vpot, rs[:, t], pc["f_t"][:, t]) / n_sub
            b_max = b_max + np.where(activo, biomasa.crecimiento(_tomar(tc["rue"], cult), vpot, rs[:, t], 1.0) / n_sub,
                                     0.0)
            db, u, fx, f_n = nitrogeno.limitar_por_n(db_w, _tomar(tc["n_biomasa"], cult), _tomar(tc["ndfa"], cult),
                                                     nitrogeno.n_disponible_raiz(n_min, z1, zp), ts["ndfa_max"])
            b, b_pot = b + db, b_pot + np.where(activo, db_pot, 0.0)
            n_min, n_planta = n_min - u, n_planta + u + fx
            f_n_ayer = np.where(activo & (db_w > 0), f_n, f_n_ayer)
            # 3c. Carbono y mineralización
            fa = agua.fraccion_disponible(w1, w1_cc, w1_pmp)
            rr = f_t_dec_base * fa
            y_antes = y
            y, o, y_n, n_min, resp, neto, _ = carbono.paso_icbm(y, o, y_n, n_min, k1d, k2d, ts["h"], rr,
                                                                 ts["cn_suelo"], dt=1.0 / n_sub)
            res_sup = res_sup * np.where(y_antes > 1e-12, y / np.maximum(y_antes, 1e-12), 1.0)
            # 3d. Lixiviación
            lix = nitrogeno.lixiviacion(n_min, d2, w1 + w2)
            n_min = n_min - lix
            for key, val in (("D", d2), ("ETa", eta), ("K", k / n_sub), ("L", lix), ("U", u), ("fx", fx),
                             ("M", neto), ("resp", resp), ("Rsat", exc), ("r", rr / n_sub)):
                acum[key] += val
        vpot_ayer = vpot

        # 4. Cosecha
        cos = prog["cosecha"][:, t]
        rend, resid, n_exp, n_res = biomasa.cosecha(b, n_planta, _tomar(tc["indice_cosecha"], cult),
                                                    _tomar(tc["indice_cosecha_n"], cult), prog["cosechar"][:, t])
        ic = np.where(prog["cosechar"][:, t], _tomar(tc["indice_cosecha"], cult), 1.0)
        rend_pot = ic * b_pot
        reg["rend_max"][:, t] = np.where(cos, ic * b_max, 0.0)
        c_in = np.where(cos, ts["fc_residuo"] * resid / 1000.0, 0.0)
        y = y + c_in
        y_n = y_n + np.where(cos, n_res, 0.0)
        res_sup = np.where(cos, np.where(prog["incorporar"][:, t], 0.0, res_sup + resid), res_sup)
        reg["rend"][:, t] = np.where(cos, rend, 0.0)
        reg["rend_pot"][:, t] = np.where(cos, rend_pot, 0.0)
        reg["b_cosecha"][:, t] = np.where(cos, b, 0.0)
        n_exportado = np.where(cos, n_exp, 0.0)
        b = np.where(cos, 0.0, b)
        b_pot = np.where(cos, 0.0, b_pot)
        b_max = np.where(cos, 0.0, b_max)
        n_planta = np.where(cos, 0.0, n_planta)
        v = np.where(cos, 0.0, v)

        # Registros (estado al final del día y flujos del día)
        reg["W"][:, t] = w1 + w2
        reg["W1"][:, t] = w1
        reg["z1"][:, t] = z1
        reg["agua_raiz"][:, t] = agua.fraccion_disponible(w1, w1_cc, w1_pmp)
        reg["N"][:, t] = n_min
        reg["C"][:, t] = y + o
        reg["B"][:, t] = b
        reg["V"][:, t] = v
        f_res_fin = cobertura.cobertura_residuo(res_sup, ts["am"])
        reg["f_residuo"][:, t] = f_res_fin
        reg["desnudo"][:, t] = cobertura.fraccion_desnuda(v, f_res_fin)
        reg["P"][:, t] = precip[:, t]
        reg["R"][:, t] = r + acum["Rsat"]
        reg["D"][:, t] = acum["D"]
        reg["I_bruto"][:, t] = i_bruto
        reg["I_neto"][:, t] = i_neto
        reg["ETa"][:, t] = acum["ETa"]
        reg["ETc"][:, t] = etc
        reg["K"][:, t] = acum["K"]
        reg["L_lix"][:, t] = acum["L"]
        reg["L_vol"][:, t] = vol
        reg["U"][:, t] = acum["U"]
        reg["fijacion"][:, t] = acum["fx"]
        reg["fert_suelo"][:, t] = fert_in
        reg["M_neta"][:, t] = acum["M"]
        reg["resp"][:, t] = acum["resp"]
        reg["c_entrada"][:, t] = c_in
        reg["r_desc"][:, t] = acum["r"]
        reg["n_entrada"][:, t] = np.where(cos, n_res, 0.0)
        reg["N_export"][:, t] = n_exportado
        reg["N_planta"][:, t] = n_planta
        reg["Y_N"][:, t] = y_n
        reg["O"][:, t] = o
        reg["res_sup"][:, t] = res_sup
    reg["inicial"] = inicial
    return reg


def equilibrio_carbono(reg: dict, k1_anual: np.ndarray, h: np.ndarray, cos: np.ndarray) -> dict:
    """Estado estacionario de ICBM bajo el manejo simulado (manejo de referencia).

    Joven: Y* = i / (k1 r̄), con i = entrada media de C (t C/ha/día) y r̄ = factor climático medio.
    Viejo: el COS medido se toma en equilibrio, lo que fija k2 efectivo = h i / (r̄ O) (por año: x 365).
    SUPUESTO: el suelo está en equilibrio con el manejo actual. Sin series de COS medidas no hay evidencia de
    una tendencia absoluta; el modelo informa diferencias respecto de ese equilibrio.
    """
    i = reg["c_entrada"].mean(1)
    r = np.maximum(reg["r_desc"].mean(1), 1e-6)
    y_medio = np.minimum(i / (k1_anual / 365.0 * r), 0.5 * cos)
    k2 = 365.0 * h * i / (r * np.maximum(cos - y_medio, 1e-9))
    # El reservorio joven y el residuo superficial oscilan dentro del año (suben en cada cosecha): el estado
    # inicial es el del 31 de diciembre de la corrida piloto, misma fase del calendario que el inicio del horizonte.
    fin_anio = np.arange(364, reg["C"].shape[1], 365)
    y_fase = (reg["C"] - reg["O"])[:, fin_anio].mean(1)
    yn_fase = reg["Y_N"][:, fin_anio].mean(1)
    y0 = np.minimum(y_fase, 0.5 * cos)
    escala = np.where(y_fase > 0, y0 / np.maximum(y_fase, 1e-12), 0.0)
    return {"y0": y0, "yn0": yn_fase * escala, "res0": reg["res_sup"][:, fin_anio].mean(1) * escala, "k2": k2}
