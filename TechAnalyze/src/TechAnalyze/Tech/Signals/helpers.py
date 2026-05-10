# Tech/signals/helpers.py
import numpy  as np
import pandas as pd

def detectar_compra(signal_array):
    signal_series = pd.Series(signal_array).fillna(0.0)
    prev = signal_series.shift(1).fillna(0.0)
    return ((signal_series == 1.0) & (prev == 0.0)).astype(float).values

def detectar_venta(signal_array):
    signal_series = pd.Series(signal_array).fillna(0.0)
    prev = signal_series.shift(1).fillna(0.0)
    activacion = (signal_series == 1.0) & (prev == 0.0)
    return np.where(activacion, -1.0, 0.0)

def high_volume(data, lookback=500, n_last=5, k=1.2):
    v = data["volume"]
    cur_mean = v.iloc[-n_last:].mean()
    base_mean = v.rolling(lookback).mean().iloc[-1]
    base_std  = v.rolling(lookback).std().iloc[-1]
    return int(cur_mean > base_mean + k*base_std)
