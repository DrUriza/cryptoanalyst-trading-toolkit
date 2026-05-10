# =====================================================
# Reduction/Reducer/data_reducer.py
# =====================================================
import pandas as pd
import numpy  as np

# === UTILIDADES  === #
def normalize_series(series):
    return (series - series.mean()) / (series.std() + 1e-6)

def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default
    
def is_finite(x):
    try:
        return np.isfinite(float(x))
    except Exception:
        return False
    
def extract_hch_pattern(hch, close_price=None):
    x = hch.get("x", [])
    y = hch.get("y", [])
    neck   = hch.get("neckline", [])
    neck_x = hch.get("neck_x", [])
    feats  = {}
    feats["type"] = -1 if hch.get("type") == "bearish" else 1
    # --- Geometría ---
    if len(x) == 3 and len(y) == 3:
        left, head, right = y
        feats["width"] = x[-1] - x[0]
        feats["symmetry"] = abs(left - right)
        height = head - (left + right) / 2
        feats["height_rel"] = height / (close_price + 1e-6) if close_price else height
    else:
        feats.update({"width": 0.0, "symmetry": 0.0, "height_rel": 0.0})

    # --- Neckline ---
    if (len(neck) == 2 and len(neck_x) == 2 and
        is_finite(neck[0]) and is_finite(neck[1]) and
        is_finite(neck_x[0]) and is_finite(neck_x[1])):
        feats["neck_slope"] = (
            (float(neck[1]) - float(neck[0])) /
            (float(neck_x[1]) - float(neck_x[0]) + 1e-6))
    else:
        feats["neck_slope"] = 0.0
    # --- Risk / Reward ---
    entry = hch.get("entry_y")
    stop  = hch.get("stop_y")
    exit_ = hch.get("exit_y")
    if is_finite(entry) and is_finite(stop) and is_finite(exit_):
        entry = float(entry)
        stop  = float(stop)
        exit_ = float(exit_)
        risk = abs(entry - stop)
        reward = abs(entry - exit_)
        rr = reward / (risk + 1e-6)
        feats["rr"] = rr if np.isfinite(rr) else 0.0
        feats["valid"] = 1 if feats["rr"] > 1 else 0
    else:
        feats.update({"rr": 0.0, "valid": 0})
    return feats

# === Decompouse Signals === #
def decompose_ta_resume(ta_resume: dict):
    feats = {}
    for ind, data in ta_resume.items():
        prefix = f"TA_{ind}"
        feats[f"{prefix}_Fza"]   = safe_float(data.get("Fza"))
        feats[f"{prefix}_Ten"]   = safe_float(data.get("Ten"))
        feats[f"{prefix}_FzaT"]  = safe_float(data.get("FzaT"))
        feats[f"{prefix}_Dir"]   = safe_float(data.get("Dir"))
        # Señales categóricas → numéricas
        signal = data.get("Signal", "NEUTRAL")
        feats[f"{prefix}_Signal"] = (1 if signal == "BUY" else -1 if signal == "SELL" else 0)
        # Extras opcionales
        if "STD" in data:
            feats[f"{prefix}_STD"] = safe_float(data.get("STD"))
        if "Delta" in data:
            feats[f"{prefix}_Delta"] = safe_float(data.get("Delta"))
    return feats

def decompose_high_volume(summary):
    return {"High_Volume": int(summary.get("High_Volume", 0))}

def decompose_trend_signals(trend):
    feats = {}
    levels = trend.get("levels", {})
    for k, v in levels.items():
        feats[f"TrendSignals_levels_{k}"] = safe_float(v)
    feats["TrendSignals_last_value"] = safe_float(trend.get("last_value"))
    signal = trend.get("signal", "NEUTRAL")
    feats["TrendSignals_signal"] = (1 if signal == "BUY" else -1 if signal == "SELL" else 0)
    return feats

def decompose_sr(sr):
    sup   = sr.get("support", [])
    res   = sr.get("resistance", [])
    feats = {}
    if sup:
        feats["SR_support_mean"] = np.mean(sup)
        feats["SR_support_std"]  = np.std(sup)
        feats["SR_support_cnt"]  = len(sup)
    else:
        feats.update({"SR_support_mean": 0, "SR_support_std":  0, "SR_support_cnt":  0})
    if res:
        feats["SR_resistance_mean"] = np.mean(res)
        feats["SR_resistance_std"]  = np.std(res)
        feats["SR_resistance_cnt"]  = len(res)
    else:
        feats.update({"SR_resistance_mean": 0, "SR_resistance_std":  0, "SR_resistance_cnt":  0})
    return feats

def decompose_fibo(fibo):
    feats = {}
    levels = fibo.get("levels", {})
    for k, v in levels.items():
        feats[f"Fibo_{k.replace('.', '_')}"] = safe_float(v)
    return feats

def decompose_hch(patterns: dict, close_price=None):
    feats = {}
    hch   = patterns.get("HCH", [])
    hchi  = patterns.get("HCHi", [])
    feats["HCH_count"]  = len(hch)
    feats["HCHi_count"] = len(hchi)
    if hch:
        last = hch[-1]
        data = extract_hch_pattern(last, close_price)
        for k, v in data.items():
            feats[f"HCH_last_{k}"] = v
    else:
        for k in ["type","width","symmetry","height_rel","neck_slope","rr","valid"]:
            feats[f"HCH_last_{k}"] = 0
    if hchi:
        last = hchi[-1]
        data = extract_hch_pattern(last, close_price)
        for k, v in data.items():
            feats[f"HCHi_last_{k}"] = v
    else:
        for k in ["type","width","symmetry","height_rel","neck_slope","rr","valid"]:
            feats[f"HCHi_last_{k}"] = 0
    return feats

def decompose_pennants(pennants: list, close_price=None):
    feats = {}
    feats["PENN_count"] = len(pennants)

    if not pennants:
        feats.update({
            "PENN_last_type": 0,
            "PENN_last_squeeze": 0.0,
            "PENN_last_spread_ratio": 0.0,
            "PENN_last_touch_balance": 0.0,
            "PENN_last_pivot_rel": 0.0,
            "PENN_last_valid": 0})
        return feats

    p = pennants[-1]
    feats["PENN_last_type"] = 1 if p.get("type") == "bull" else -1
    spread_start = safe_float(p.get("spread_start"))
    spread_end   = safe_float(p.get("spread_end"))
    feats["PENN_last_squeeze"] = safe_float(p.get("squeeze"))
    feats["PENN_last_spread_ratio"] = (
        spread_end / (spread_start + 1e-6) if spread_start > 0 else 0.0)

    up = safe_float(p.get("touch_up"))
    dn = safe_float(p.get("touch_dn"))
    feats["PENN_last_touch_balance"] = (up - dn) / (up + dn + 1e-6)

    pivot = p.get("pivot", {})
    pivot_y = safe_float(pivot.get("y"))
    feats["PENN_last_pivot_rel"] = (
        pivot_y / (close_price + 1e-6) if close_price else pivot_y)

    feats["PENN_last_valid"] = int(feats["PENN_last_squeeze"] < 0.2 and feats["PENN_last_spread_ratio"] < 0.3)
    return feats

# === PROCESS FEATURES === #
def build_process_data_features(df):
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[f"{col}_norm"] = normalize_series(df[col])
    df["vol_ratio"]    = df["buy_volume"] / (df["sell_volume"] + 1e-6)
    df["spread_rel"]   = (df["high"] - df["low"]) / (df["close"] + 1e-6)
    return df

# === TARGETS LABELS === #
def add_targets(df, atr_factor: 0.5):
    close = next((c for c in ["close", "close_x", "close_y"] if c in df.columns),None)
    if close is None:
        return df
    df = df.copy()
    next_close = df[close].shift(-1).ffill()
    df["future_return"] = next_close / df[close] - 1
    df["dynamic_threshold"] = df["ATR"] * atr_factor / (df[close] + 1e-6)
    df["target_bin"] = np.where(df["future_return"] > df["dynamic_threshold"],  1, np.where(df["future_return"] < -df["dynamic_threshold"], -1, 0))
    return df

# === MASTER DF (LOGIC ONLY)  === #
def build_master_dataframe(process_df, summary_df, ob_flat, ob_metrics, ob_state, atr_factor):
    if process_df is None:
        process_df = pd.DataFrame()
    process_df   = process_df.copy().reset_index(drop=True)
    min_len      = len(process_df)
    process_df   = process_df.iloc[:min_len].reset_index(drop=True)
    pr_feat   = build_process_data_features(process_df)
    data_ft   = add_targets(pr_feat, atr_factor=atr_factor)
    df_master = merge (data_ft, summary_df, ob_flat, ob_metrics, ob_state) 
    return df_master

def decompose_summary(summary, close_price=None):
    feats = {}
    if "TA_Resume" in summary:
        feats.update(decompose_ta_resume(summary["TA_Resume"]))
    if "TrendSignals" in summary:
        feats.update(decompose_trend_signals(summary["TrendSignals"]))
    if "Patterns" in summary:
        feats.update(decompose_hch(summary["Patterns"], close_price))
        if "SR" in summary["Patterns"]:
            feats.update(decompose_sr(summary["Patterns"]["SR"]))
        if "Fibo" in summary["Patterns"]:
            feats.update(decompose_fibo(summary["Patterns"]["Fibo"]))
        if "Pennants" in summary["Patterns"]:
            feats.update(decompose_pennants(summary["Patterns"]["Pennants"], close_price))
    feats.update(decompose_high_volume(summary))
    return feats

def decompose_orderbook(ob_flat, ob_metrics, ob_state):
    feats = {}
    # -------- METRICS --------
    if ob_metrics is not None and not ob_metrics.empty:
        row = ob_metrics.iloc[0].to_dict()
        for k, v in row.items():
            feats[f"OBM_{k}"] = safe_float(v)
    # -------- FLAT (DEPTH) --------
    if ob_flat is not None and not ob_flat.empty:
        row = ob_flat.iloc[0].to_dict()
        bid_qty = []
        ask_qty = []
        for k, v in row.items():
            if "bid_qty" in k:
                bid_qty.append(safe_float(v))
            if "ask_qty" in k:
                ask_qty.append(safe_float(v))
        feats["OBF_bid_liquidity"] = sum(bid_qty)
        feats["OBF_ask_liquidity"] = sum(ask_qty)
        feats["OBF_liquidity_imbalance"] = ((feats["OBF_bid_liquidity"] - feats["OBF_ask_liquidity"]) / 
                                            (feats["OBF_bid_liquidity"] + feats["OBF_ask_liquidity"] + 1e-6))
    # -------- STATES (EVENTOS → ÚLTIMO) --------
    if ob_state is not None and not ob_state.empty:
        last = ob_state.iloc[-1].to_dict()
        signal = last.get("signal", "NEUTRAL")
        feats["OBS_signal"] = (1 if signal == "BUY" else -1 if signal == "SELL" else 0)
        feats["OBS_pressure"] = safe_float(last.get("pressure"))
    return feats

# === Fusion de archivos  === #
def merge(data_ft, summary_df, ob_flat, ob_metrics, ob_state):
    # --- base temporal ---
    base = data_ft.copy().reset_index(drop=True)
    n = len(base)
    # --- precios de referencia ---
    close_price = base["close"].iloc[-1] if "close" in base else None
    # --- SUMMARY ---
    summary_row   = summary_df.iloc[0].to_dict() if summary_df is not None and not summary_df.empty else {}
    summary_feats = decompose_summary(summary_row, close_price)
    summary_exp   = pd.DataFrame([summary_feats] * n)
    # --- ORDERBOOK ---
    ob_feats = decompose_orderbook(ob_flat, ob_metrics, ob_state)
    ob_exp   = pd.DataFrame([ob_feats] * n)
    # --- MASTER ---
    df_master = pd.concat([base, summary_exp, ob_exp], axis=1)
    return df_master

# === FILTRO CORRELACIONAL  === #
def correlation_filter(df, name, threshold=0.92):
    if df is None or df.empty:
        print(f"[Correlation] {name}: DataFrame vacío")
        return df
    if df.shape[0] < 2:
        print(f"[Correlation] {name}: insuficientes filas para correlación")
        return df
    protected_cols = ["target_bin", "future_return", "dynamic_threshold", "trend_score"]
    protected_present = [c for c in protected_cols if c in df.columns]
    df_protected = df[protected_present]
    df_features  = df.drop(columns=protected_present, errors="ignore")
    df_num = (df_features.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0))
    if df_num.shape[1] < 2:
        return pd.concat([df_features, df_protected], axis=1)
    corr  = df_num.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [c for c in upper.columns if (upper[c] > threshold).any()]
    df_clean = df_features.drop(columns=to_drop, errors="ignore")
    df_final = pd.concat([df_clean, df_protected], axis=1)
    print(f"🟣 [Correlation] {name}: eliminadas {len(to_drop)} columnas")
    return df_final
