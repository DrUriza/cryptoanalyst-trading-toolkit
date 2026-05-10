# =====================================================
# Tech/Analyzers/kalman.py
# =====================================================
import numpy as np
import pandas as pd


def Kalman_Filter(data):
    """
    Kalman Filter CAUSAL:
    - NO usa predicción futura
    - NO mezcla pasado/futuro
    - len(output) == len(data)
    """
    idx = data.index
    n   = len(data)
    # --------------------------------------------
    # Inicializar salidas (regla de oro)
    # --------------------------------------------
    OpenE  = pd.Series(np.nan, index=idx)
    HighE  = pd.Series(np.nan, index=idx)
    LowE   = pd.Series(np.nan, index=idx)
    CloseE = pd.Series(np.nan, index=idx)
    # --------------------------------------------
    # Observaciones
    # --------------------------------------------
    prices = np.vstack([
        data["open"].to_numpy(),
        data["high"].to_numpy(),
        data["low"].to_numpy(),
        data["close"].to_numpy()
    ]).T

    n_steps, n_vars = prices.shape

    # --------------------------------------------
    # Parámetros Kalman
    # --------------------------------------------
    process_var     = 1e-5
    measurement_var = 0.1

    F = np.block([
        [np.eye(n_vars), np.eye(n_vars)],
        [np.zeros((n_vars, n_vars)), np.eye(n_vars)]
    ])

    H = np.block([
        np.eye(n_vars),
        np.zeros((n_vars, n_vars))
    ])

    Q = process_var * np.eye(2 * n_vars)
    R = measurement_var * np.eye(n_vars)

    # --------------------------------------------
    # Estado inicial (solo t=0)
    # --------------------------------------------
    x = np.hstack([prices[0], np.zeros(n_vars)])
    P = np.eye(2 * n_vars) * 0.1

    # --------------------------------------------
    # Filtro CAUSAL
    # --------------------------------------------
    for i in range(n_steps):

        z = prices[i]

        # Prediction
        x_pred = F @ x
        P_pred = F @ P @ F.T + Q

        # Update
        y = z - H @ x_pred
        S = H @ P_pred @ H.T + R
        K = P_pred @ H.T @ np.linalg.inv(S)

        x = x_pred + K @ y
        P = (np.eye(2 * n_vars) - K @ H) @ P_pred

        # Guardar SOLO estado estimado actual
        OpenE.iloc[i]  = x[0]
        HighE.iloc[i]  = x[1]
        LowE.iloc[i]   = x[2]
        CloseE.iloc[i] = x[3]

    return OpenE, CloseE, LowE, HighE
