# =====================================================
# Tech/fusion/fusion_pipeline.py
# =====================================================
import pandas as pd

INDICATORS = ["BB-M", "ADX", "TSI", "RSI", "STK", "STKs", "MA-S", "MA-E", "MA-N", "ATR", "WD", "MACD"]

TREND_MAP = {
    "BB-M":  "PosicionBB-R",
    "ADX":   "PosicionADX",
    "TSI":   "PosicionTSI",
    "RSI":   "PosicionRSI",
    "STK":   "PosicionSTK",
    "STKs":  "PosicionSTKs",
    "MA-S":  "PosicionMM-S",
    "MA-E":  "PosicionMM-E",
    "MA-N":  "PosicionMM-N",
    "MACD":  "PosicionMACD",
    "WD":    "PosicionWD"
}

# =====================================================
# CONFIG DE COLUMNAS (TU JSON REAL)
# =====================================================
PRICE_COL = "close"   # en tu JSON es 'close' (minúscula)

# Bollinger en tu JSON:
BB_UP_COL  = "BB-A"   # banda superior
BB_LOW_COL = "BB-B"   # banda inferior
BB_MID_COL = "BB-M"   # media (opcional, no imprescindible)

# =====================================================
# HELPERS
# =====================================================
def _clean(series):
    if series is None:
        return pd.Series([], dtype="float64")
    return pd.to_numeric(series, errors="coerce").dropna()

def _safe_last(series):
    if series is None:
        return None
    s = pd.to_numeric(series, errors="coerce").dropna()
    return None if s.empty else float(s.iloc[-1])

def _clip(x, lo=0.0, hi=100.0):
    try:
        v = float(x)
    except Exception:
        v = 0.0
    return float(max(lo, min(hi, v)))

def _last_signal(df: pd.DataFrame, col: str):
    """
    Encuentra el ÚLTIMO valor no-cero en col, regresa (signo, idx)
    signo ∈ {-1, +1}
    Si no encuentra, regresa (0, None)
    """
    if col not in df.columns:
        return 0, None

    for i in reversed(range(len(df))):
        v = df.iloc[i][col]
        if pd.isna(v):
            continue
        v = float(v)
        if v == 0:
            continue
        return (1 if v > 0 else -1), i
    return 0, None

def _slope_recent(s: pd.Series, win: int = 6):
    if s is None or len(s) < 2:
        return 0.0, 0
    w = max(2, int(win))
    tail = s.iloc[-w:] if len(s) >= w else s
    diffs = tail.diff().dropna()
    if diffs.empty:
        return 0.0, 0
    slope = float(diffs.mean())
    sign = 1 if slope > 0 else (-1 if slope < 0 else 0)
    return slope, sign

def _color_from_dir(dir_sign: int):
    # Direccionales: NUNCA gris
    return ("green", 1) if dir_sign >= 0 else ("red", -1)

def _strength_minmax_clamped(s: pd.Series, dir_sign: int, eps: float = 1e-12):
    """
    Fza 0..100 basada en la posición del ÚLTIMO valor dentro de su rango histórico.
    - Si dir_sign > 0: más alto => más fuerte (0..100)
    - Si dir_sign < 0: más bajo => más fuerte (0..100)
    """
    if s is None or len(s) < 2:
        return 0.0

    val = float(s.iloc[-1])
    vmin = float(s.min())
    vmax = float(s.max())
    rng = max(vmax - vmin, eps)
    p = (val - vmin) / rng          # 0..1
    p = max(0.0, min(1.0, p))

    if dir_sign > 0:
        fza = 100.0 * p
    elif dir_sign < 0:
        fza = 100.0 * (1.0 - p)
    else:
        # si plano, fuerza por distancia a centro
        fza = 100.0 * abs(p - 0.5) * 2.0

    return _clip(fza, 0.0, 100.0)

# =====================================================
# BOLLINGER (TU REGLA):
# - max/min lo dan LAS BANDAS (UP/LOW)
# - si precio está pegado arriba -> ROJO (retroceso probable)
# - si precio está pegado abajo  -> VERDE (rebote probable)
# - si está en medio -> GRIS (neutral)
# Fza = qué tan cerca estás de una banda (0 centro, 100 borde)
# =====================================================
def _bb_now_state(
    data: pd.DataFrame,
    price_col: str = PRICE_COL,
    up_col: str = BB_UP_COL,
    low_col: str = BB_LOW_COL,
    mid_zone: float = 0.20,   # 0.20 => 20% central es “neutral” (ajústalo)
    eps: float = 1e-12
):
    if price_col not in data.columns or up_col not in data.columns or low_col not in data.columns:
        return None

    c = _safe_last(data[price_col])
    u = _safe_last(data[up_col])
    l = _safe_last(data[low_col])
    if c is None or u is None or l is None:
        return None

    bw = max(u - l, eps)
    pos01 = (c - l) / bw      # 0..1 (ideal)
    pos01 = max(0.0, min(1.0, pos01))

    # Fuerza: 0 en el centro (0.5), 100 en los bordes (0 o 1)
    fza = _clip(abs(pos01 - 0.5) * 2.0 * 100.0, 0.0, 100.0)

    # Neutral zone: alrededor del centro
    lo_neutral = 0.5 - mid_zone
    hi_neutral = 0.5 + mid_zone

    if pos01 >= hi_neutral:
        # cerca de la banda superior => rojo (retroceso)
        color = "red"
        direction = -1
        ten = -1
        reason = "NEAR_UPPER"
    elif pos01 <= lo_neutral:
        # cerca de la banda inferior => verde (rebote)
        color = "green"
        direction = +1
        ten = +1
        reason = "NEAR_LOWER"
    else:
        # en medio => gris permitido SOLO en BB
        color = "gray"
        direction = 0
        ten = 0
        reason = "MIDDLE"

    extra = {
        "BB_pos01": round(pos01, 4),
        "BB_reason": reason,
        "BB_up": round(u, 2),
        "BB_low": round(l, 2),
        "BB_bw": round(bw, 6),
    }
    return ten, fza, direction, color, extra

# =====================================================
# PIPELINE PRINCIPAL
# =====================================================
def techtable(data: pd.DataFrame):
    n = len(data)
    snapshot = {}
    if n < 2:
        return snapshot

    for ind in INDICATORS:

        # ---------------- BB (replanteado) ----------------
        if ind == "BB-M":
            bb = _bb_now_state(data)
            if bb is None:
                continue

            ten, fza, direction, color, extra = bb

            # BB es estado actual, no evento histórico:
            fzaT = 100.0

            snapshot[ind] = {
                "Fza": round(_clip(fza, 0.0, 100.0), 2),
                "Ten": int(ten),  # puede ser 0 SOLO en BB (middle)
                "FzaT": round(_clip(fzaT, 0.0, 100.0), 2),
                "Signal": ("BUY" if ten > 0 else ("SELL" if ten < 0 else "NEUTRAL")),
                "Dir": int(direction),
                "Color": color,
                **extra
            }
            continue

        # ---------------- resto ----------------
        if ind not in data.columns:
            continue

        s = _clean(data[ind])
        if s.empty:
            continue

        # (1) Dirección principal: SIEMPRE verde/rojo para direccionales
        trend_col = TREND_MAP.get(ind)
        ten_evt, idx_evt = _last_signal(data, trend_col) if trend_col else (0, None)

        # Si no hay evento, usa slope; si slope es 0, default +1 (nunca gris)
        slope, slope_sign = _slope_recent(s, win=6)
        dir_sign = ten_evt if ten_evt != 0 else (slope_sign if slope_sign != 0 else 1)

        # (2) Color/dirección:
        # WD puede ser gris en medio (si tú quieres neutral ahí)
        if ind == "WD":
            # regla simple: si WD está cerca del centro del rango -> gris
            # (ajústalo si ya tienes tu lógica de WD)
            fza_dir = _strength_minmax_clamped(s, dir_sign)
            # neutral si fuerza pequeña (en medio)
            if fza_dir < 15.0:
                color, direction = "gray", 0
            else:
                color, direction = _color_from_dir(dir_sign)
        else:
            color, direction = _color_from_dir(dir_sign)

        # (3) Fza: del último valor (normalizada 0..100, CLAMP)
        fza = _strength_minmax_clamped(s, dir_sign)

        # (4) FzaT: “tiempo/recencia” del último evento (0..100, CLAMP)
        if idx_evt is None or n <= 1:
            fzaT = 0.0
        else:
            fzaT = (idx_evt / (n - 1)) * 100.0
        fzaT = _clip(fzaT, 0.0, 100.0)

        extra = {}
        if ind == "STK":
            std_val = _safe_last(data.get("STD"))
            stk_val = _safe_last(data.get("STK"))
            if std_val is not None and stk_val is not None:
                extra["STD"] = round(std_val, 2)
                extra["Delta"] = round(stk_val - std_val, 2)

        if ind == "STKs":
            stds_val = _safe_last(data.get("STDs"))
            stks_val = _safe_last(data.get("STKs"))
            if stds_val is not None and stks_val is not None:
                extra["STD"] = round(stds_val, 2)
                extra["Delta"] = round(stks_val - stds_val, 2)

        snapshot[ind] = {
            "Fza": round(_clip(fza, 0.0, 100.0), 2),
            "Ten": int(dir_sign),  # nunca 0 en direccionales (excepto BB, y WD si neutral)
            "FzaT": round(_clip(fzaT, 0.0, 100.0), 2),
            "Signal": ("BUY" if direction > 0 else ("SELL" if direction < 0 else "NEUTRAL")),
            "Dir": int(direction),
            "Color": color,
            "Slope": round(float(slope), 8),
            "SlopeSign": int(1 if slope > 0 else (-1 if slope < 0 else 0)),
            **extra
        }

    return snapshot