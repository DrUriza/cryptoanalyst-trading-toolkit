# =====================================================
# Tech/Orderbook/features/features.py
# =====================================================
import numpy as np

def extract_pressure(ob_df, max_levels=20):
    if ob_df is None or not hasattr(ob_df, "iloc") or len(ob_df) == 0:
        return None

    row = ob_df.iloc[-1]

    bid_liq = 0.0
    ask_liq = 0.0

    for i in range(1, max_levels + 1):
        bq = row.get(f"bid_qty_{i}")
        aq = row.get(f"ask_qty_{i}")

        if bq is not None and not np.isnan(bq):
            bid_liq += float(bq)
        if aq is not None and not np.isnan(aq):
            ask_liq += float(aq)

    if bid_liq > 0 and ask_liq > 0:
        return round(bid_liq / ask_liq, 3)

    return None


def compute_basic_ob_metrics(ob_df, max_levels=20):
    if ob_df is None or not hasattr(ob_df, "iloc") or len(ob_df) == 0:
        return {}
    row  = ob_df.iloc[-1]
    bids = []
    asks = []
    for i in range(1, max_levels + 1):
        bp = row.get(f"bid_price_{i}")
        bq = row.get(f"bid_qty_{i}")
        ap = row.get(f"ask_price_{i}")
        aq = row.get(f"ask_qty_{i}")
        if bp is not None and bq is not None and not np.isnan(bp) and not np.isnan(bq):
            bids.append((float(bp), float(bq)))
        if ap is not None and aq is not None and not np.isnan(ap) and not np.isnan(aq):
            asks.append((float(ap), float(aq)))
    if not bids or not asks:
        return {}
    bids_sorted = sorted(bids, key=lambda x: x[0])
    asks_sorted = sorted(asks, key=lambda x: x[0])
    best_bid = bids_sorted[-1][0]
    best_ask = asks_sorted[0][0]
    bid_liq = sum(q for _, q in bids_sorted)
    ask_liq = sum(q for _, q in asks_sorted)
    spread = best_ask - best_bid
    mid_price = (best_bid + best_ask) / 2
    imbalance = (bid_liq / (bid_liq + ask_liq) if (bid_liq + ask_liq) > 0 else 0.5)
    return {
        "ob_best_bid": best_bid,
        "ob_best_ask": best_ask,
        "ob_mid_price": mid_price,
        "ob_spread": spread,
        "ob_bid_liquidity": bid_liq,
        "ob_ask_liquidity": ask_liq,
        "ob_imbalance": imbalance
    }

def compute_ob_deltas(prev_metrics, cur_metrics):
    """
    prev_metrics/cur_metrics = dict de compute_basic_ob_metrics
    """
    if not prev_metrics or not cur_metrics:
        return {}

    def g(d, k, default=np.nan):
        v = d.get(k, default)
        return float(v) if v is not None else default

    best_bid_delta = g(cur_metrics, "ob_best_bid") - g(prev_metrics, "ob_best_bid")
    best_ask_delta = g(cur_metrics, "ob_best_ask") - g(prev_metrics, "ob_best_ask")
    mid_delta      = g(cur_metrics, "ob_mid_price") - g(prev_metrics, "ob_mid_price")

    bid_liq_delta  = g(cur_metrics, "ob_bid_liquidity") - g(prev_metrics, "ob_bid_liquidity")
    ask_liq_delta  = g(cur_metrics, "ob_ask_liquidity") - g(prev_metrics, "ob_ask_liquidity")

    return {
        "ob_best_bid_delta": best_bid_delta,
        "ob_best_ask_delta": best_ask_delta,
        "ob_mid_delta": mid_delta,
        "ob_bid_liq_delta": bid_liq_delta,
        "ob_ask_liq_delta": ask_liq_delta,
    }

def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return np.nan

def compute_pulling_stacking(prev_ob_df, cur_ob_df, max_levels=2):
    """
    Para IB L2, usa max_levels=2.
    Pulling = caída de qty (quitan liquidez).
    Stacking = aumento de qty (agregan liquidez).
    """
    if prev_ob_df is None or cur_ob_df is None or prev_ob_df.empty or cur_ob_df.empty:
        return {}

    p = prev_ob_df.iloc[-1]
    c = cur_ob_df.iloc[-1]

    bid_pull = bid_stack = 0.0
    ask_pull = ask_stack = 0.0

    for i in range(1, max_levels+1):
        pbq = _safe_float(p.get(f"bid_qty_{i}"))
        cbq = _safe_float(c.get(f"bid_qty_{i}"))
        paq = _safe_float(p.get(f"ask_qty_{i}"))
        caq = _safe_float(c.get(f"ask_qty_{i}"))

        if not np.isnan(pbq) and not np.isnan(cbq):
            d = cbq - pbq
            if d < 0: bid_pull += abs(d)
            else:     bid_stack += d

        if not np.isnan(paq) and not np.isnan(caq):
            d = caq - paq
            if d < 0: ask_pull += abs(d)
            else:     ask_stack += d

    return {
        "bid_pulling": round(bid_pull, 6),
        "bid_stacking": round(bid_stack, 6),
        "ask_pulling": round(ask_pull, 6),
        "ask_stacking": round(ask_stack, 6),
    }
