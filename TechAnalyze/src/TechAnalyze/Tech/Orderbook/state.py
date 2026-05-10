# =====================================================
# Tech/Orderbook/state/state.py
# =====================================================
import time
from datetime import datetime
import pandas as pd

MAX_HISTORY = 100

def classify_ob_signal_v2(pressure, deltas, buy_th=1.1, sell_th=0.9):
    """
    Regla conservadora:
    - Si best bid se está cayendo => SELL aunque pressure diga BUY
    - Si best bid estable/subiendo y pressure BUY => BUY
    """
    if pressure is None:
        return "NEUTRAL"
    best_bid_delta = deltas.get("ob_best_bid_delta", 0.0)
    mid_delta      = deltas.get("ob_mid_delta", 0.0)
    # Si el bid se está corriendo hacia abajo y el mid cae: bajista real
    if best_bid_delta < 0 and mid_delta < 0:
        return "SELL"
    # Si el bid deja de caer y hay presión compradora (liquidez)
    if pressure > buy_th and best_bid_delta >= 0:
        return "BUY"
    if pressure < sell_th:
        return "SELL"
    return "NEUTRAL"

def update_ob_state(ob_sta, pressure, deltas=None, pull=None):
    if isinstance(ob_sta, pd.DataFrame) and not ob_sta.empty:
        history = ob_sta.to_dict(orient="records")
    else:
        history = []

    signal = classify_ob_signal_v2(pressure, deltas or {})
    entry = {"time": datetime.fromtimestamp(time.time()).strftime("%H:%M:%S"),"signal": signal,"pressure": pressure}

    if deltas:
        entry.update(deltas)
    if pull:
        entry.update(pull)

    history.append(entry)
    history = history[-MAX_HISTORY:]
    return history


