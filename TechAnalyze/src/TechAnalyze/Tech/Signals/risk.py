# =====================================================
# Tech/Signals/risk.py
# =====================================================

def StopLoss_TakeProfit(data):
        close = data['close'].iloc[-1]
        atr   = data['ATR'].iloc[-1]
        adx   = data['ADX'].iloc[-1]
        mdp   = data['MD+'].iloc[-1]
        mdm   = data['MD-'].iloc[-1]
        # Peso direccional normalizado
        if (mdp + mdm) != 0:
            strength_up   = mdp / (mdp + mdm)
            strength_down = mdm / (mdp + mdm)
        else:
            strength_up = strength_down = 0.5
        sl_distance = 1.5 * atr
        # Ratio dinámico según tendencia (ADX)
        if adx > 25:
            rr_ratio = 2.0   # tendencia fuerte → más ambicioso
        else:
            rr_ratio = 1.2   # tendencia débil → más conservador
        # Definición según direccionalidad
        if mdp > mdm:  # señal alcista
            stop_loss  = close - sl_distance
            take_profit = close + sl_distance * rr_ratio * (1 + strength_up/2)
        elif mdp < mdm:  # señal bajista
            stop_loss  = close + sl_distance
            take_profit = close - sl_distance * rr_ratio * (1 + strength_down/2)
        else:  # sin dirección clara
            stop_loss  = close - atr
            take_profit = close + atr
        return stop_loss, take_profit