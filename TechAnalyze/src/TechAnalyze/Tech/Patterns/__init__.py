# =====================================================
# Tech/Patterns/__init__.py
# Centraliza importación de patrones
# =====================================================

# ---- Candle Classification ----
from .candles import classify_candle

# ---- Head & Shoulders / HCH / HCHi ----
from .candles import detect_head_shoulders, build_hs_struct

# ---- Fibonacci Levels ----
from .candles import build_fibo_struct

# ---- Support & Resistance ----
from .candles import build_sr_struct

# ---- Pennants / Continuation Patterns ----
from .candles import build_pennants_struct

# =====================================================
# Exposición ordenada de métodos disponibles
# =====================================================
__all__ = [
    "classify_candle",
    "detect_head_shoulders",
    "build_hs_struct",
    "build_fibo_struct",
    "build_sr_struct",
    "build_pennants_struct",
]
