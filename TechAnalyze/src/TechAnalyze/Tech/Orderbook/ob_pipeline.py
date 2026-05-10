# =====================================================
# OrderBook Pipeline - versión modular unificada
# =====================================================
from .feature import extract_pressure, compute_basic_ob_metrics, compute_ob_deltas, compute_pulling_stacking
from .state   import update_ob_state

def orderbook_pipeline(ob_fla, ob_sta, prev_ob_fla=None, prev_metrics=None, max_levels=2):
    # ================== METRICS ==================
    metrics = compute_basic_ob_metrics(ob_fla, max_levels)
    # ================== PRESSURE ==================
    pressure = extract_pressure(ob_fla, max_levels)
    # ================== DELTAS ==================
    deltas = compute_ob_deltas(prev_metrics or {}, metrics)
    # ================== PULLING/STACKING ==================
    pull = compute_pulling_stacking(prev_ob_fla, ob_fla, max_levels=max_levels)
    # ================== STATE UPDATE ==================
    state = update_ob_state(ob_sta, pressure, deltas=deltas, pull=pull)
    return metrics, deltas, pull, state
