# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Balance hídrico W(t) en dos capas: zona radicular (espesor z1 variable) y resto del perfil (zp - z1).

dW/dt = P + I - ET - R - D, con W = W1 + W2 en mm. Funciones vectorizadas sobre miembros del ensamble.
Base: FAO-56 cap. 8 (Ks, RAW, riego), TR-55 (escorrentía), AquaCrop (drenaje tau).
"""
import numpy as np

EPS = 1e-9


def almacenamiento(theta, z_m):
    """Agua en mm de una capa de espesor z_m con contenido volumétrico theta (m³/m³)."""
    return 1000.0 * np.asarray(theta) * np.asarray(z_m)


def redistribuir(w1, w2, z1_antes, z1_despues, zp):
    """Cambio de espesor de la zona radicular conservando agua.

    Si las raíces profundizan, pasa a la capa 1 la fracción de W2 del espesor ganado; si la zona se reduce
    (cosecha), pasa a la capa 2 la fracción de W1 del espesor perdido. Supone contenido uniforme en cada capa.
    """
    crece = z1_despues > z1_antes
    f_gana = np.where(crece, (z1_despues - z1_antes) / np.maximum(zp - z1_antes, EPS), 0.0)
    f_pierde = np.where(crece, 0.0, (z1_antes - z1_despues) / np.maximum(z1_antes, EPS))
    mov = f_gana * w2 - f_pierde * w1
    return w1 + mov, w2 - mov


def p_ajustado(p_tabla, etc, ajuste=0.04):
    """Fracción de agotamiento sin estrés corregida por ETc (FAO-56 Tabla 22, nota), acotada a 0,1-0,8."""
    return np.clip(p_tabla + ajuste * (5.0 - etc), 0.1, 0.8)


def coef_estres(w1, w1_cc, w1_min, umbral_mm):
    """Coeficiente de estrés hídrico (FAO-56 ec. 84) o de reducción de evaporación (ec. 74), 0-1.

    K = 1 mientras el agotamiento D = W1_cc - W1 no supera el umbral (RAW o REW); después baja linealmente
    hasta 0 cuando se agota toda el agua disponible A = W1_cc - W1_min.
    """
    a = np.maximum(w1_cc - w1_min, EPS)
    d = np.clip(w1_cc - w1, 0.0, a)
    u = np.minimum(umbral_mm, a)
    k = np.where(d <= u, 1.0, (a - d) / np.maximum(a - u, EPS))
    return np.clip(k, 0.0, 1.0)


def riego_automatico(activo, w1, w1_cc, raw, umbral, usado_mm, tope_mm, eficiencia):
    """Riego que repone la zona radicular a capacidad de campo si el agotamiento supera umbral * RAW.

    Devuelve (neto, bruto) en mm; bruto = neto / eficiencia y respeta el tope bruto de la temporada.
    """
    agot = np.maximum(w1_cc - w1, 0.0)
    dispara = activo & (agot > umbral * raw) & (agot > 0)
    disponible_bruto = np.maximum(tope_mm - usado_mm, 0.0)
    neto = np.where(dispara, np.minimum(agot, disponible_bruto * eficiencia), 0.0)
    return neto, neto / eficiencia


def infiltrar(w1, w2, entrada, w1_sat, w2_sat):
    """Agua que entra por la superficie. El exceso sobre saturación de la capa 1 pasa a la 2; el de la 2 escurre."""
    w1 = w1 + entrada
    exc1 = np.maximum(w1 - w1_sat, 0.0)
    w1 = w1 - exc1
    w2 = w2 + exc1
    exc2 = np.maximum(w2 - w2_sat, 0.0)
    return w1, w2 - exc2, exc2


def drenaje(w, w_cc, tau):
    """Drenaje por gravedad del exceso sobre capacidad de campo (AquaCrop): tau * max(W - W_cc, 0)."""
    return tau * np.maximum(w - w_cc, 0.0)


def tau_subpaso(tau, n_sub: int):
    """tau equivalente para n subpasos, tal que n subpasos sin otros flujos drenen lo mismo que un día."""
    return 1.0 - (1.0 - np.asarray(tau)) ** (1.0 / n_sub)


def evapotranspiracion(w1, w1_min, et_pot, k):
    """ET real = K * ET potencial, sin extraer agua bajo el mínimo extraíble (no negatividad)."""
    return np.minimum(k * et_pot, np.maximum(w1 - w1_min, 0.0))


def fraccion_disponible(w, w_cc, w_pmp):
    """Agua disponible relativa (0 en punto de marchitez, 1 en capacidad de campo)."""
    return np.clip((w - w_pmp) / np.maximum(w_cc - w_pmp, EPS), 0.0, 1.0)
