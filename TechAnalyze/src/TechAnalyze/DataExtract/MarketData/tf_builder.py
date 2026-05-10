import pandas as pd
import numpy  as np

def build_tf(df_m1, block, n_candles=500):
    required = n_candles * block
    df_src   = df_m1.tail(required).reset_index(drop=True)
    data     = []
    for i in range(0, len(df_src), block):
        group = df_src.iloc[i:i+block]
        if len(group) < block:
            break
        # --- Dirección y fuerza ---
        delta    = group["close"] - group["open"]
        range_   = (group["high"] - group["low"]).replace(0, 1e-6)
        strength = (delta.abs() / range_).clip(0, 1)
        # --- Reparto de volumen (SIN mutar group) ---
        buy_vol = np.where(
            delta >= 0,
            group["volume"] * (0.5 + 0.5 * strength),
            group["volume"] * (0.5 - 0.5 * strength))
        sell_vol = group["volume"] - buy_vol
        data.append({
            "timestamp": int(group.iloc[-1]["timestamp"]),
            "open":      group.iloc[0]["open"],
            "close":     group.iloc[-1]["close"],
            "high":      group["high"].max(),
            "low":       group["low"].min(),
            # Coherencia de volumen
            "volume":      group["volume"].mean(),
            "buy_volume":  buy_vol.sum(),
            "sell_volume": sell_vol.sum(),
            "spread":      group["spread"].mean(),
            "color": "green" if group.iloc[-1]["close"] >= group.iloc[0]["open"] else "red"})
    result = pd.DataFrame(data).tail(n_candles).reset_index(drop=True)
    print(f"TF {block}m → generado {len(result)} velas finales usando {required} M1")
    return result
