# =====================================================
# Tech/indicators/momentum.py
# =====================================================
import numpy           as np
import pandas          as pd
from ta.momentum       import rsi, tsi
from ..Signals.helpers import detectar_compra, detectar_venta

def RSI_TSI(data):
        dataRSI = rsi(data['close'], 14, False)
        dataTSI = tsi(data['close'])
        dataSenalRSI    = np.where(dataRSI < 35, 1.0, np.where(dataRSI > 75, -1.0, 0.0))
        dataPosicionRSI = pd.Series(dataSenalRSI)
        dataPosicionRSI = np.where((dataPosicionRSI != 0), dataPosicionRSI, 0.0)
        dataTSI_series  = pd.Series(dataTSI)
        # Señales de cruce
        cruce_menor_25    = (dataTSI_series < 25)
        cruce_mayor_25    = (dataTSI_series > 25) 
        cruce_arriba_cero = (dataTSI_series > 0)
        cruce_abajo_cero  = (dataTSI_series < 0)
        dataPosicionTSID  = np.select([cruce_menor_25, cruce_mayor_25],[0.0, -1.0],default=0.0)
        dataPosicionTSIU  = np.select([cruce_arriba_cero, cruce_abajo_cero],[0.0, 1.0],default=0.0)
        dataPosicionTSI =   np.select([(dataPosicionTSIU == 1.0) & (dataTSI_series < 0), 
                                    (dataPosicionTSID == -1.0) & (dataTSI_series > 25),] ,[1.0, -1.0], default=0.0)
        return dataRSI, dataTSI, dataPosicionRSI, dataPosicionTSI

def Stochastic_OscillatorFast(data, k_window=14, d_window=3):
    low_min  = data['low'].rolling(window=k_window).min()
    high_max = data['high'].rolling(window=k_window).max()

    # %K y %D
    K_fast = 100 * (data['close'] - low_min) / (high_max - low_min + 1e-9)
    D_fast = K_fast.rolling(window=d_window).mean()

    # Eventos
    buy_signal  = (K_fast < 20) & (K_fast > D_fast)
    sell_signal = (K_fast.shift(1) > 80) & (K_fast < D_fast)

    position = np.zeros(len(data))
    current_pos = 0  # estado inicial

    for i in range(len(data)):
        if buy_signal.iloc[i]:
            current_pos = 1
        elif sell_signal.iloc[i]:
            current_pos = -1
        # else: mantiene la posición anterior

        position[i] = current_pos

    return K_fast, D_fast, position


def Stochastic_OscillatorSlow(data, k_window=14, d_window=3):
    low_min  = data['low'].rolling(window=k_window).min()
    high_max = data['high'].rolling(window=k_window).max()
    K_raw    = 100 * (data['close'] - low_min) / (high_max - low_min + 1e-9)
    K_slow   = K_raw.rolling(window=d_window).mean()
    D_slow   = K_slow.rolling(window=d_window).mean()
    buy_signal  = (K_slow < 25) & (K_slow > D_slow)
    sell_signal = (K_slow.shift(1) > 80) & (K_slow < D_slow)
    position = np.zeros(len(data))
    current_pos = 0
    for i in range(len(data)):
        if buy_signal.iloc[i]:
            current_pos = 1
        elif sell_signal.iloc[i]:
            current_pos = -1
        position[i] = current_pos
    return K_slow, D_slow, position
