# =====================================================
# Tech/indicators/trend.py
# =====================================================
import numpy     as np
import pandas    as pd
from ta.trend    import SMAIndicator, EMAIndicator, WMAIndicator
from itertools   import product
from joblib      import Parallel, delayed

# ---------- Helpers ----------
def strategy(MAs, ma_type, data):  
        df = data.copy()
        df['retornos'] = df['close'].pct_change()
        short_MA, long_MA = int(MAs[0]), int(MAs[1])
        if short_MA >= long_MA:
            return -np.inf  # Invalid parameters
        # Calculate moving averages based on ma_type
        if ma_type == 'SMA':
            df['short'] = SMAIndicator(df['close'], short_MA).sma_indicator()
            df['long']  = SMAIndicator(df['close'], long_MA).sma_indicator()
        elif ma_type == 'EMA':
            df['short'] = EMAIndicator(df['close'], short_MA).ema_indicator()
            df['long']  = EMAIndicator(df['close'], long_MA).ema_indicator()
        elif ma_type == 'WMA':
            df['short'] = WMAIndicator(df['close'], short_MA).wma()
            df['long']  = WMAIndicator(df['close'], long_MA).wma()
        else:
            raise ValueError("Invalid ma_type. Choose 'SMA', 'EMA', or 'WMA'.")
        # Fill NaN values from moving averages to avoid missing data
        df[['short', 'long']] = df[['short', 'long']].fillna(method='bfill')
        # Generate trading positions: 1 for long, -1 for short
        df['posicion'] = np.where(df['short'] > df['long'], 1, -1)
        # Apply position strategy to returns with a one-period lag
        df['estrategia'] = df['posicion'].shift(1) * df['retornos']
        # Remove rows with NaN values
        df.dropna(inplace=True)
        # Calculate cumulative return
        cumulative_strategy_return = np.exp(df['estrategia'].sum())
        return -cumulative_strategy_return  # Negative for optimization

def parallel_brute(func, ranges, data, ma_type):
        """Parallel brute-force optimization."""
        grid_points = list(product(*ranges))
        # Ensure correct function call with arguments
        results = Parallel(n_jobs=-1, prefer="threads")(delayed(func)(point, ma_type, data) for point in grid_points)
        best_idx = np.argmin(results)
        return grid_points[best_idx], results[best_idx]

def optimize(ma_type, data):
    grid = list(product(range(5,75), range(40,250)))
    res = Parallel(n_jobs=-1, prefer="threads")(
        delayed(strategy)(g, ma_type, data) for g in grid)
    return grid[int(np.argmin(res))]

def compute_weighted_score(new_trend, history):
        """Calcula score continuo de tendencia ponderada"""
        history.append(new_trend)
        n = len(history)
        # Pesos decrecientes
        if n == 1:
            weights = [1.0]
        elif n == 2:
            weights = [0.75, 0.25]
        elif n == 3:
            weights = [0.66, 0.22, 0.12]
        elif n == 4:
            weights = [0.6, 0.2, 0.13, 0.07]
        elif n == 5:
            weights = [0.55, 0.15, 0.12, 0.1, 0.08]
        else:
            base = 0.5 / (n - 1)
            weights = [0.5] + [base] * (n - 1)
        weights = np.array(weights) / np.sum(weights)
        mapping = {"alcista": 1.0, "lateral": 0.0, "bajista": -1.0}
        scores  = [mapping[t] for t in history]
        return float(np.dot(weights, scores))

def classify_block(block_df):
        """Clasifica un bloque de 500 velas como alcista, bajista o lateral"""
        open_macro  = block_df["open"].iloc[0]
        close_macro = block_df["close"].iloc[-1]
        if close_macro > open_macro:
            return "alcista"
        elif close_macro < open_macro:
            return "bajista"
        else:
            return "lateral"

# ---------- Public ----------
def WMM(data):
        # Define the parameter ranges for short and long moving averages (periods)
        param_ranges = [(5, 75), (40, 250)]
        params, _    = parallel_brute(strategy, param_ranges, ma_type='WMA', data=data)
        short_period, long_period = int(params[0]), int(params[1])  
        dataMA_S = WMAIndicator(data['close'], int(short_period), False).wma()
        dataMA_L = WMAIndicator(data['close'], int(long_period), False).wma()
        # Creamos una nueva columna de cruces
        dataSenalMM       = np.where(dataMA_L > dataMA_S, 1.0, 0.0)
        dataSenalMM_Serie = pd.Series(dataSenalMM, index=data.index)
        dataPosicionMM = dataSenalMM_Serie.diff().fillna(0.0)  
        dataMA_N          = (dataMA_S + dataMA_L)/2
        return dataMA_S, dataMA_L, dataPosicionMM, dataMA_N

def EMM(data):
        # Define the parameter ranges for short and long moving averages (periods)
        param_ranges = [(5, 75), (40, 250)]
        params, _    = parallel_brute(strategy, param_ranges, ma_type='EMA', data=data)
        short_period, long_period = int(params[0]), int(params[1])   
        dataMA_E_S = EMAIndicator(data['close'], window=int(short_period)).ema_indicator()
        dataMA_E_L = EMAIndicator(data['close'], window=int(long_period)).ema_indicator()
        # Creamos una nueva columna de cruces
        dataSenalMM_E       = np.where(dataMA_E_L > dataMA_E_S, 1.0, 0.0)
        dataSenalMM_E_Serie = pd.Series(dataSenalMM_E, index=data.index)
        dataPosicionMM_E = dataSenalMM_E_Serie.diff().fillna(0.0)  
        dataMA_E            = (dataMA_E_S + dataMA_E_L)/2
        return dataMA_E_S, dataMA_E_L, dataPosicionMM_E, short_period, long_period, dataMA_E

def SMM(data):
        # Define the parameter ranges for short and long moving averages (periods)
        param_ranges = [(5, 75), (40, 250)]
        params, _    = parallel_brute(strategy, param_ranges, ma_type='SMA', data=data)
        short_period, long_period = int(params[0]), int(params[1])
        dataSMA_S = SMAIndicator(data['close'], short_period, False).sma_indicator()
        dataSMA_L = SMAIndicator(data['close'], long_period, False).sma_indicator()
        dataSenalMM_S    = np.where(dataSMA_L > dataSMA_S, 1.0, 0.0)
        dataSenalMM_S_Serie = pd.Series(dataSenalMM_S, index=data.index)
        dataPosicionMM_S = dataSenalMM_S_Serie.diff().fillna(0.0)  
        dataMA_S         = (dataSMA_S + dataSMA_L)/2
        return dataSMA_S, dataSMA_L, dataPosicionMM_S, dataMA_S

def MACDMM(data, short_periodE, long_periodE):
        dataMA_E_S = EMAIndicator(data['close'], window=short_periodE).ema_indicator()
        dataMA_E_L = EMAIndicator(data['close'], window=long_periodE).ema_indicator()
        # MACD calculation
        dataMACD = dataMA_E_S - dataMA_E_L
        dataSignal = dataMACD.ewm(span=short_periodE, adjust=False).mean()
        # Generate buy/sell signal
        dataSenalMACD = np.where(dataMACD > dataSignal, 1.0, 0.0)
        dataSenalMACD_Serie = pd.Series(dataSenalMACD, index=data.index)  # Keep index alignment
        dataPosicionMACD = dataSenalMACD_Serie.diff().fillna(0.0)  
        return dataMACD, dataSignal, dataPosicionMACD

def build_trending_struct(data, q_strong=0.90, q_mid=0.65):
    ft     = data["FullTrend"].dropna()
    strong = ft.quantile(q_strong)
    mid    = ft.quantile(q_mid)
    levels = {"strong_buy":  float(strong),
              "buy":         float(mid),
              "sell":       -float(mid),
              "strong_sell":-float(strong)}
    last = ft.iloc[-1]
    if   last >= levels["strong_buy"]:
        signal = "STRONG SELL"
    elif last >= levels["buy"]:
        signal = "SELL"
    elif last <= levels["strong_sell"]:
        signal = "STRONG BUY"
    elif last <= levels["sell"]:
        signal = "BUY"
    else:
        signal = "NEUTRAL"
    return {"levels": levels, "last_value": float(last), "signal": signal}

def TrendB(data, step=5):
    scores = []
    for i in range(0, len(data), step):
        blk = data.iloc[i:i+step]
        if len(blk) < step:
            break
        ret = (blk["close"].iloc[-1] - blk["open"].iloc[0]) / blk["open"].iloc[0]
        val = np.tanh(ret * 10)   
        scores.extend([val] * step)
    if len(scores) < len(data):
        scores.extend([scores[-1]] * (len(data) - len(scores)))
    return pd.Series(scores[:len(data)], index=data.index)

def TrendA(data, step=2):
    scores = []
    for i in range(0, len(data), step):
        blk = data.iloc[i:i+step]
        if len(blk) < step:
            break
        ret = (blk["close"].iloc[-1] - blk["open"].iloc[0]) / blk["open"].iloc[0]
        val = np.tanh(ret * 25)   # más sensible (trend rápido)
        scores.extend([val] * step)
    # asegurar longitud exacta
    if len(scores) < len(data):
        scores.extend([scores[-1]] * (len(data) - len(scores)))
    return pd.Series(scores[:len(data)], index=data.index)
