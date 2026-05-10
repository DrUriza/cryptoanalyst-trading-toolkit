# =====================================================
# Tech/patterns/candles.py
# Candle + Chart Patterns (H&S)
# =====================================================
import numpy      as np
from scipy.signal import argrelextrema

# ---------- Helpers ----------
def classify_candle(data):
    # Cálculos vectorizados
        body               = abs(data['close'] - data['open'])
        total_range        = (data['high'] - data['low']).replace(0, np.nan) # Evitar divisiones por cero
        upper_shadow       = data['high'] - data[['close', 'open']].max(axis=1)
        lower_shadow       = data[['close', 'open']].min(axis=1) - data['low']
        body_ratio         = body / total_range
        upper_shadow_ratio = upper_shadow / total_range
        lower_shadow_ratio = lower_shadow / total_range
        # Crear condiciones booleanas
        is_bullish = data['close'] > data['open']
        is_bearish = ~is_bullish
        conditions = [(is_bullish & (body_ratio > 0.7) & (upper_shadow_ratio < 0.1) & (lower_shadow_ratio > 0.2)),
                    (is_bullish & (body_ratio > 0.6) & (lower_shadow_ratio > upper_shadow_ratio * 1.5)),
                    (is_bullish & (body_ratio > 0.6) & (upper_shadow_ratio > lower_shadow_ratio * 1.5)),
                    (is_bullish & (body_ratio > 0.4)),
                    (is_bullish),
                    (is_bearish & (body_ratio > 0.7) & (lower_shadow_ratio < 0.1) & (upper_shadow_ratio > 0.2)),
                    (is_bearish & (body_ratio > 0.6) & (upper_shadow_ratio > lower_shadow_ratio * 1.5)),
                    (is_bearish & (body_ratio > 0.6) & (lower_shadow_ratio > upper_shadow_ratio * 1.5)),
                    (is_bearish & (body_ratio > 0.4)),
                    (is_bearish)]
        choices = ['Strong Bullish','Strong Bullish Lower','Bullish Resistance','Bullish','Low Bullish',
                'Strong Bearish','Strong Bearish Lower','Bullish Support','Bearish','Low Bearish']
        # Aplicar las condiciones
        Candle = np.select(conditions, choices, default='Unknown')
        return Candle

# =====================================================
#   H&S detection + JSON
# =====================================================
def detect_head_shoulders(data, order):
    """
    Detecta patrones H&S y H&S invertido.
    Retorna lista de dicts con estructura del patrón.
    """
    prices = data['close'].values
    idx    = data.index
    # máximos y mínimos locales
    highs   = argrelextrema(prices, np.greater, order=order)[0]
    lows    = argrelextrema(prices, np.less,    order=order)[0]
    signals = []
    # ---------- H&S (techo) ----------
    for i in range(len(highs) - 2):
        h1, h2, h3 = highs[i:i+3]
        if prices[h2] > prices[h1] and prices[h2] > prices[h3]:
            neckline = np.mean([prices[l] for l in lows if h1 < l < h3] or [])
            if neckline:
                signals.append({"type": "H&S", "pattern": (h1, h2, h3, neckline), "time": idx[h3]})
    # ---------- H&S invertido ----------
    for i in range(len(lows) - 2):
        l1, l2, l3 = lows[i:i+3]
        if prices[l2] < prices[l1] and prices[l2] < prices[l3]:
            neckline = np.mean([prices[h] for h in highs if l1 < h < l3] or [])
            if neckline:
                signals.append({"type": "H&S_INV", "pattern": (l1, l2, l3, neckline), "time": idx[l3]})
    return signals

def build_hs_struct(data, order=10, rr=1.8):
    signals  = detect_head_shoulders(data, order)
    patterns = {"HCH":[], "HCHi":[]}
    idx      = list(data.index)
    closes   = data['close'].values
    for s in signals:
        h1,h2,h3,neckline = s["pattern"]
        p1,p2,p3 = closes[[h1,h2,h3]]
        if s["type"]=="H&S":
            entry_day  = h3
            entry_price= neckline*0.997
            stop_loss  = p2*1.01
            exit_price = entry_price - (stop_loss-entry_price)*rr
            patterns["HCH"].append({"x":[idx[h1],idx[h2],idx[h3]],
                                    "y":[float(p1), float(p2), float(p3)],
                                    "neckline":[float(neckline)]*2,
                                    "neck_x":[idx[h1],idx[h3]],
                                    "entry_x":idx[h3], "entry_y":float(entry_price),
                                    "stop_y": float(stop_loss),
                                    "exit_y": float(exit_price),
                                    "type":"bearish"})
        if s["type"]=="H&S_INV":
            entry_day  = h3
            entry_price= neckline*1.003
            stop_loss  = p2*0.99
            exit_price = entry_price + (entry_price-stop_loss)*rr
            patterns["HCHi"].append({"x":[idx[h1],idx[h2],idx[h3]],
                                     "y":[float(p1), float(p2), float(p3)],
                                     "neckline":[float(neckline)]*2,
                                     "neck_x":[idx[h1],idx[h3]],
                                     "entry_x":idx[entry_day], "entry_y":float(entry_price),
                                     "stop_y": float(stop_loss),
                                     "exit_y": float(exit_price),
                                     "type":"bullish" })
    return patterns

# =====================================================
#  Fibonacci Structure for JSON export
# =====================================================
def build_fibo_struct(data):
    swing_high = data['high'].max()
    swing_low  = data['low'].min()
    fib_levels = {"0.0":  float(swing_low),
                  "0.236": float(swing_low + (swing_high-swing_low)*0.236),
                  "0.382": float(swing_low + (swing_high-swing_low)*0.382),
                  "0.5":   float(swing_low + (swing_high-swing_low)*0.5),
                  "0.618": float(swing_low + (swing_high-swing_low)*0.618),
                  "0.786": float(swing_low + (swing_high-swing_low)*0.786),
                  "1.0":   float(swing_high)}
    return {"levels": fib_levels}

# =====================================================
#   Support / Resistance detection + JSON
# =====================================================
def build_sr_struct(data, max_levels=5, sensitivity=3):
    closes = data['close'].values
    idx    = data.index
    pivots_high = argrelextrema(closes, np.greater, order=sensitivity)[0]
    pivots_low  = argrelextrema(closes, np.less,    order=sensitivity)[0]
    levels_res  = sorted([float(closes[i]) for i in pivots_high])[-max_levels:]
    levels_sup  = sorted([float(closes[i]) for i in pivots_low])[:max_levels]
    return {"support": levels_sup, "resistance": levels_res}

# =====================================================
# Pennants detector para JSON
# =====================================================
def build_pennants_struct(data, lookback=60, min_touch=3, max_squeeze=0.35, rng=40):
    closes   = data['close'].values
    highs    = data['high'].values
    lows     = data['low'].values
    idx      = list(data.index)
    pennants = []
    for i in range(lookback, len(data)):
        seg_high = highs[i-lookback:i]
        seg_low  = lows[i-lookback:i]
        # slope superior e inferior
        x = np.arange(lookback)
        up_slope, up_int = np.polyfit(x, seg_high,  1)
        dn_slope, dn_int = np.polyfit(x, seg_low,   1)
        # convergencia
        if up_slope >= 0 or dn_slope <= 0:  
            continue
        spread_start = seg_high[0] - seg_low[0]
        spread_end   = seg_high[-1] - seg_low[-1]
        squeeze = spread_end / spread_start
        if squeeze > max_squeeze:
            continue
        touches_up = sum(seg_high >= (up_slope*x + up_int)*0.995)
        touches_dn = sum(seg_low  <= (dn_slope*x + dn_int)*1.005)
        if touches_up < min_touch or touches_dn < min_touch:
            continue
        # Breakout
        last_close = closes[i]
        up_line    = up_slope*lookback + up_int
        dn_line    = dn_slope*lookback + dn_int
        if last_close > up_line:
            direction="bull"
        elif last_close < dn_line:
            direction="bear"
        else:
            continue
        a = max(0, i-rng)
        b = i
        c = min(len(data)-1, i+rng)
        pennants.append({"index": int(i),
                         "type": direction,
                         "upper_x":[idx[a],idx[b],idx[c]],
                         "upper_y":[float(closes[a]+up_slope*rng), float(closes[b]), float(closes[c]-up_slope*rng)],
                         "lower_x":[idx[a],idx[b],idx[c]],
                         "lower_y":[float(closes[a]-dn_slope*rng), float(closes[b]), float(closes[c]+dn_slope*rng)],
                         "pivot":{"x":idx[b], "y":float(closes[b])},
                         "spread_start": float(spread_start),
                         "spread_end": float(spread_end),
                         "squeeze": float(squeeze),
                         "touch_up": int(touches_up),
                         "touch_dn": int(touches_dn)})
    return pennants
