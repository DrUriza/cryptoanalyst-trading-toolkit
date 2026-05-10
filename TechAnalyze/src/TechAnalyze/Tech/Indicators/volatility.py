# =====================================================
# Tech/indicators/volatility.py
# =====================================================
import pandas               as pd
import numpy                as np
from ta.volatility          import AverageTrueRange
from ta.volatility          import BollingerBands
from ta.trend               import ADXIndicator

def ATR(data):
        atr = AverageTrueRange(data['high'], data['low'], data['close'], 20, False).average_true_range()
        return atr

def ADX(data):
        dataADX = ADXIndicator(data['high'], data['low'], data['close'], 14, False).adx()
        dataMDU = ADXIndicator(data['high'], data['low'], data['close'], 14, False).adx_pos()
        dataMDD = ADXIndicator(data['high'], data['low'], data['close'], 14, False).adx_neg()
        # Creamos una nueva columna de cruces ADXM+ & ADXM-
        dataSenalMD = np.where(dataMDU > dataMDD, 1.0, 0.0)
        # Convert to a Pandas Series to compute .diff()
        dataSenalMD_series = pd.Series(dataSenalMD)
        # Compute the difference (to detect changes in the signal)
        dataPosicionMD = dataSenalMD_series.diff()
        return dataADX, dataMDU, dataMDD,dataPosicionMD

def BB(data):
        # Dynamically calculate the Bollinger Bands window size
        bollinger_window  = max(5, len(data) // 10)  # Example: Use 10% of the data length, with a minimum of 5
        bollinger_std_dev = 2  # Standard deviation factor, typically 2
        # Add Bollinger Bands data to the DataFrame
        dataBB_A = BollingerBands(data['close'], window=bollinger_window, window_dev=bollinger_std_dev).bollinger_hband()  # Upper band
        dataBB_B = BollingerBands(data['close'], window=bollinger_window, window_dev=bollinger_std_dev).bollinger_lband()  # Lower band
        dataBB_M = BollingerBands(data['close'], window=bollinger_window, window_dev=bollinger_std_dev).bollinger_mavg()   # Moving average (middle band)
        dataSenalBB_R    = np.where(dataBB_M > data['y_pred'], 1.0, 0.0)
        dataSenalBB_R_series = pd.Series(dataSenalBB_R, index=data.index)
        dataPosicionBB_R     = dataSenalBB_R_series.diff().fillna(0.0)
        return dataBB_A, dataBB_B, dataBB_M, dataPosicionBB_R
