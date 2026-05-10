# =====================================================
# Components/plots_manager.py (Versión Final Unificada)
# Integra dashboard + single plots + H&S + Pennants
# =====================================================
from dash                   import html, dcc
import plotly.graph_objects as go
from plotly.subplots        import make_subplots
import pandas               as pd

class PlotManager:
    def __init__(self, traces):
        print("✅ PlotManager inicializado")
        self.traces = traces
    # ==========================================================
    # DASHBOARD COMPLETO
    # ==========================================================
    def build_dashboard(self, asset, zoom, data_source, sf=10):
        data, summary = self.traces.update_market_data(asset, zoom, data_source)
        P = summary.get("Patterns", {})
        trend_pack = summary.get("TrendSignals", {})
        if data.empty:
            return html.Div([html.H3("⚠ No data"), html.P("Verifica Process_Data_*.json")])
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, row_heights=[0.50,0.15,0.15,0.15], vertical_spacing=0.024)
        # ---------------- CANDLE ----------------
        fig.add_trace(go.Candlestick(x=data.index, open=data['open'], high=data['high'], low=data['low'], close=data['close'], name=f"Price: {data['close'].iloc[-1]}"), row=1, col=1)
        fig.update_xaxes(rangeslider_visible=False)
        # ---------------- MOVING AVERAGES ----------------
        def L(y,name,color):
            fig.add_trace(go.Scatter(x=data.index,y=y,mode='lines', line=dict(color=color,width=1),name=name,showlegend=False),row=1,col=1)
        L(data['MA-S-S'],'MA-S-S','green')
        L(data['MA-S-L'],'MA-S-L','red')
        L(data['MA-S'],  'MA-S','black')
        L(data['MA-L'],  'MA-L','magenta')
        L(data['MA-E-S'],'MA-E-S','blue')
        L(data['MA-E-L'],'MA-E-L','orange')
        fig.add_trace(go.Scatter(x=data.index,y=data['BB-A'],line=dict(color='grey',width=1),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=data.index,y=data['BB-B'],fill='tonexty',line=dict(color='grey'),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=data.index,y=data['BB-M'],line=dict(color='brown'),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=data.index,y=data['y_pred'],line=dict(color='yellow'),showlegend=False),row=1,col=1)
        # ================== FIBONACCI ==================
        fibo = P.get("Fibo", {}).get("levels", {})
        for lvl, price in fibo.items():
            if price is None or pd.isna(price):
                continue
            # Línea horizontal de lado a lado del panel
            fig.add_shape(type="line",xref="x domain", yref="y", x0=0, x1=1, y0=price, y1=price, line=dict(color="blue", width=1, dash="dash"), row=1, col=1)
            fig.add_annotation(xref="x domain", yref="y", x=1.002, y=price,text=f"Fib {lvl}",showarrow=False, font=dict(color="black", size=12), row=1, col=1)
        # ================== SUPPORT & RESISTANCE ==================
        sr = P.get("SR", {})
        for s in sr.get("support", []):
            if s is None or pd.isna(s):
                continue
            fig.add_shape(type="line", xref="x domain", yref="y", x0=0, x1=1,y0=s,y1=s, line=dict(color="green", width=1, dash="dot"), row=1, col=1)
        for r in sr.get("resistance", []):
            if r is None or pd.isna(r):
                continue
            fig.add_shape(type="line", xref="x domain", yref="y", x0=0, x1=1, y0=r, y1=r, line=dict(color="red", width=1, dash="dot"), row=1, col=1)
        # ---------------- ENTRY SIGNALS ----------------
        def M(mask,y,name,color,symbol,row,col):
            fig.add_trace(go.Scatter(x=data[mask].index, y=y[mask],mode='markers', marker=dict(color=color,size=15,symbol=symbol),name=name),row=row,col=col)
            fig.update_xaxes(rangeslider_visible=False)
        # ------------------------------------
        # CONFIG PANEL INDEX
        # ------------------------------------
        row = 1
        col = 1
        # ---------------- PRICE PANEL ----------------
        M(data['PosicionMM-S']==1 , data['MA-S-S'], 'Up-MS'  ,'green'  ,'star-triangle-up'  ,row,col)
        M(data['PosicionMM-S']==-1, data['MA-S-L'], 'Down-MS','red'    ,'star-triangle-down',row,col)
        M(data['PosicionMM-N']==1 , data['MA-S']  , 'Up-M'   ,'black'  ,'star-triangle-up'  ,row,col)
        M(data['PosicionMM-N']==-1, data['MA-L']  , 'Down-M' ,'magenta','star-triangle-down',row,col)
        M(data['PosicionMM-E']==1 , data['MA-E-S'],'Up-ME'  ,'blue'   ,'star-triangle-up'  ,row,col)
        M(data['PosicionMM-E']==-1, data['MA-E-L'],'Down-ME','orange' ,'star-triangle-down',row,col)
        M(data['PosicionBB-R']==-1, data['y_pred'], 'Up-R'  ,'brown'  ,'star-triangle-up'  ,row,col)
        M(data['PosicionBB-R']==1 , data['BB-M']  , 'Down-R','yellow' ,'star-triangle-down',row,col)
        # ---------------- ADX PANEL ----------------
        row = 2 ; col = 1     
        fig.add_trace(go.Scatter(x=data.index,y=data['ADX'], line=dict(color='black'),showlegend=False), row=row,col=col)
        fig.add_trace(go.Scatter(x=data.index,y=data['MD+'], line=dict(color='green'),showlegend=False), row=row,col=col)
        fig.add_trace(go.Scatter(x=data.index,y=data['MD-'], line=dict(color='red'),showlegend=False), row=row,col=col)
        M(data['PosicionADX']==1 , data['MD+'], 'Up-ADX'  ,'gold' ,'star-triangle-up'  ,row,col)
        M(data['PosicionADX']==-1, data['MD-'], 'Down-ADX','cyan' ,'star-triangle-down',row,col)
        # ---------------- VOLUME ----------------
        row = 3 ; col = 1
        fig.add_trace(go.Bar(x=data.index, y=data['volume'], name="Volume", marker=dict(color=data['Color'], opacity=0.60), 
                             showlegend=True), row=row, col=col)
         # ----------------ORDER VOLUME ----------------
        row = 4 ; col = 1
        # BUY como negativo (hacia abajo)
        fig.add_trace(go.Bar(x=data.index, y=-data['buy_volume'], name="Buy Volume",marker=dict(color='rgba(0,200,0,0.70)'), 
                             showlegend=True), row=row, col=col)
        # SELL como positivo (hacia arriba)
        fig.add_trace(go.Bar(x=data.index, y=data['sell_volume'], name="Sell Volume", marker=dict(color='rgba(220,0,0,0.70)'),
                             showlegend=True), row=row, col=col)
        # 💠 OrderFlow neto (solo si existe en JSON)
        if 'OrderFlow' in data.columns:
            fig.add_trace(go.Scatter(x=data.index, y=data['OrderFlow'], mode="lines", line=dict(width=1, color="cyan"), 
                                     name="OrderFlow Trend"), row=row, col=col)
        # Layout final
        fig.update_layout(height=1000,margin=dict(l=20,r=20,t=30,b=20))
        # ==============================================================================
        # SEGUNDO PANEL (RSI, Trend, WD, ATR, Kalman, Pennants, H&S, MACD & Stochastic)
        # ==============================================================================
        fig2 = make_subplots(rows=3, cols=3, shared_xaxes=True,vertical_spacing=.05,horizontal_spacing=.075)
        # RSI
        fig2.add_trace(go.Scatter(x=data.index,y=data['RSI'],line=dict(color='black'), showlegend=False),row=1,col=1)
        fig2.add_trace(go.Scatter(x=data.index,y=[35]*len(data),line=dict(color='green', dash='dash'), showlegend=False),row=1,col=1)
        fig2.add_trace(go.Scatter(x=data.index,y=[75]*len(data),line=dict(color='red', dash='dash'), showlegend=False),row=1,col=1)
        # Trending 
        fig2.add_trace(go.Scatter(x=data.index, y=data["FullTrend"], mode="lines", name="Full Trend", line=dict(color="blue"),showlegend=False),row=1, col=2)
        trend_pack = summary.get("TrendSignals", {})
        levels     = trend_pack.get("levels", {})
        level_defs = [("strong_buy",  "#00B050"),  # Verde fuerte
                      ("buy",         "#92D050"),  # Verde claro
                      ("sell",        "#FFC000"),  # Naranja/Amarillo
                      ("strong_sell", "#C00000")]  # Rojo fuerte
        x0, x1 = data.index[0], data.index[-1]
        for key, col in level_defs:
            lvl = levels.get(key)
            if lvl is None:
                continue
            fig2.add_trace(go.Scatter(x=[x0, x1], y=[lvl, lvl], mode="lines", line=dict(color=col, width=1, dash="dash"), showlegend=False,hoverinfo="skip"),row=1, col=2)
        # WD
        fig2.add_trace(go.Scatter(x=data.index,y=data['WD'],line=dict(color='black'),showlegend=False),row=1,col=3)
        # ATR
        fig2.add_trace(go.Scatter(x=data.index,y=data['ATR'],line=dict(color='black'),showlegend=False),row=2,col=1)
        # Kalman
        fig2.add_trace(go.Candlestick(x=data.index,open=data['OpenE'],high=data['HighE'],low=data['LowE'],close=data['CloseE'], showlegend=False),row=2,col=2)
        fig2.update_xaxes(rangeslider_visible=False, row=2, col=2)
        # TSI
        fig2.add_trace(go.Scatter(x=data.index, y=data['TSI'], line=dict(color='black'), name="TSI", showlegend=False), row=2, col=3)
        fig2.add_trace(go.Scatter(x=data.index, y=[-20]*len(data),line=dict(color='green', dash='dash'), showlegend=False), row=2, col=3)
        fig2.add_trace(go.Scatter(x=data.index, y=[35]*len(data), line=dict(color='red', dash='dash'), showlegend=False), row=2, col=3)
        # MACD 
        fig2.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='black', width=1), name="MACD", showlegend=False), row=3, col=1)
        fig2.add_trace(go.Scatter(x=data.index, y=data['SignalMACD'], line=dict(color='#90EE90', width=1), name="Signal MACD", showlegend=False), row=3, col=1)
        macd_pos = 6*(data['MACD'] - data['SignalMACD']).clip(lower=0)
        macd_neg = 6*(data['MACD'] - data['SignalMACD']).clip(upper=0)
        fig2.add_trace(go.Bar(x=data.index, y=macd_pos, marker_color='green', showlegend=False), row=3, col=1)
        fig2.add_trace(go.Bar(x=data.index, y=macd_neg, marker_color='red', showlegend=False), row=3, col=1)
        fig2.add_trace(go.Scatter(x=data[data['PosicionMACD']==1].index, y=data['MACD'][data['PosicionMACD']==1],
                                  mode='markers', marker=dict(size=12,color='lime',symbol='star-triangle-up'),
                                  name="MACD Buy", showlegend=False), row=3,col=1)
        fig2.add_trace(go.Scatter(x=data[data['PosicionMACD']==-1].index, y=data['MACD'][data['PosicionMACD']==-1],
                                  mode='markers', marker=dict(size=12,color='red',symbol='star-triangle-down'),
                                  name="MACD Sell", showlegend=False), row=3,col=1)
        # Stochastic
        fig2.add_trace(go.Scatter(x=data.index,y=data['STK'], line=dict(color='brown'), name='Fast %K',showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index,y=data['STD'], line=dict(color='black'), name='Fast %D',showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index,y=data['STKs'], line=dict(color='#F30000'), name='Slow %K',showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index,y=data['STDs'], line=dict(color='#00309E'), name='Slow %D',showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index,y=[80]*len(data), line=dict(color='red',dash='dash'),showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index,y=[20]*len(data), line=dict(color='blue',dash='dash'),showlegend=False), row=3, col=2)
        buyF  = (data['PosicionSTK']==1)   & (data['STK']<20)
        sellF = (data['PosicionSTK']==-1)  & (data['STD']>80)
        buyS  = (data['PosicionSTKs']==1)  & (data['STKs']<20)
        sellS = (data['PosicionSTKs']==-1) & (data['STDs']>80)
        fig2.add_trace(go.Scatter(x=data.index[buyF], y=data['STK'][buyF],
                                mode='markers',marker=dict(size=12,color="lime",symbol='star-triangle-up'),showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index[sellF],y=data['STD'][sellF],
                                mode='markers',marker=dict(size=12,color="red",symbol='star-triangle-down'),showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index[buyS],y=data['STKs'][buyS],
                                mode='markers',marker=dict(size=12,color="#026B02",symbol='arrow-up'),showlegend=False), row=3, col=2)
        fig2.add_trace(go.Scatter(x=data.index[sellS],y=data['STDs'][sellS],
                                mode='markers',marker=dict(size=12,color="#480000",symbol='arrow-down'),showlegend=False), row=3, col=2)
        # -----------------------------------------------------------
        # H&S + PENNANTS
        # -----------------------------------------------------------
        fig2.add_trace(go.Candlestick(x=data.index,open=data['open'],high=data['high'],low=data['low'],close=data['close'], showlegend=False),row=3,col=3)
        def H(arr, color):
            n = len(data)
            for p in arr:
                if ("x" not in p or "y" not in p or len(p["x"]) != len(p["y"]) or any(pd.isna(p["y"]))):
                    continue

                valid_pos = [k for k, i in enumerate(p["x"]) if 0 <= i < n and not pd.isna(p["y"][k])]
                if len(valid_pos) < 2:
                    continue

                X = [data.index[p["x"][k]] for k in valid_pos]
                Y = [p["y"][k] for k in valid_pos]

                fig2.add_trace(
                    go.Scatter(x=X, y=Y,mode='lines+markers', line=dict(color=color, width=2), showlegend=False), row=3, col=3)

                if p.get("neckline") and p.get("neck_x") and len(p["neck_x"]) == 2 and not any(pd.isna(p["neckline"])):
                    if 0 <= p["neck_x"][0] < n and 0 <= p["neck_x"][1] < n:
                        NX = [data.index[p["neck_x"][0]], data.index[p["neck_x"][1]]]
                        fig2.add_trace(go.Scatter(x=NX, y=p["neckline"], mode="lines", line=dict(color=color, dash="dash"), showlegend=False), row=3, col=3)

        H(P.get("HCH", []), "red")
        H(P.get("HCHi", []), "lime")
        for p in P.get("Pennants", []):
            n = len(data)

            upper_pos = [k for k, i in enumerate(p.get("upper_x", [])) if 0 <= i < n and k < len(p.get("upper_y", [])) and not pd.isna(p["upper_y"][k])]
            lower_pos = [k for k, i in enumerate(p.get("lower_x", [])) if 0 <= i < n and k < len(p.get("lower_y", [])) and not pd.isna(p["lower_y"][k])]

            UX = [data.index[p["upper_x"][k]] for k in upper_pos]
            UY = [p["upper_y"][k] for k in upper_pos]

            LX = [data.index[p["lower_x"][k]] for k in lower_pos]
            LY = [p["lower_y"][k] for k in lower_pos]

            if len(UX) >= 2 and len(UY) >= 2:
                fig2.add_trace(go.Scatter(x=UX, y=UY, mode="lines", line=dict(color="orange"), showlegend=False), row=3, col=3)
            if len(LX) >= 2 and len(LY) >= 2:
                fig2.add_trace(go.Scatter(x=LX, y=LY, mode="lines", line=dict(color="orange"), showlegend=False), row=3, col=3)

            if "pivot" in p and isinstance(p["pivot"], dict) and "x" in p["pivot"] and "y" in p["pivot"]:
                if 0 <= p["pivot"]["x"] < n and not pd.isna(p["pivot"]["y"]):
                    fig2.add_trace(go.Scatter(x=[data.index[p["pivot"]["x"]]], y=[p["pivot"]["y"]], mode="markers", marker=dict(color="orange",
                                                                                                                        size=9,
                                                                                                                        symbol="diamond"),
                                                                                                                        showlegend=False),
                                                                                                                        row=3, col=3)
        fig2.update_layout(height=800)
        for r in range(1,4):
            for c in range(1,4):
                fig2.update_xaxes(rangeslider_visible=False, row=r, col=c)
        fig2.update_layout(height=800)
        fig2.update_layout(showlegend=False)
        return html.Div([dcc.Graph(figure=fig),dcc.Graph(figure=fig2)])
    # ==========================================================
    # SINGLE-PLOT REQUEST (/plot/<id>)
    # ==========================================================
    def build_single_plot(self, plot_type, asset, zoom, data_source):
        print("📊 Single plot:", plot_type)
        data, summary  = self.traces.update_market_data(asset, zoom, data_source)
        P = summary.get("Patterns", {})
        trend_pack = summary.get("TrendSignals", {})
        fig  = go.Figure()
        # ---------------- RSI ----------------
        if plot_type == "RSI":
            fig.add_trace(go.Scatter(x=data.index, y=[35]*len(data), line=dict(color="green"), name="Buy", showlegend=True))
            fig.add_trace(go.Scatter(x=data.index, y=[75]*len(data), line=dict(color="red"), name="Sell", showlegend=True))
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color="black"), name="RSI", showlegend=True))
        # ---------------- TSI ----------------
        elif plot_type == "TSI":
            fig.add_trace(go.Scatter(x=data.index, y=data['TSI'], line=dict(color="black"), name="TSI", showlegend=True))
            fig.add_trace(go.Scatter(x=data.index, y=[-20]*len(data), line=dict(color="green"), name="Buy"))
            fig.add_trace(go.Scatter(x=data.index, y=[35]*len(data), line=dict(color="red"), name="Sell"))
        # ---------------- Wasserstein Distance ----------------
        elif plot_type == "WD":
            fig.add_trace(go.Scatter(x=data.index,y=data['WD'],line=dict(color='black'),name="W-Distance", showlegend=True))
        # ---------------- ATR ----------------
        elif plot_type == "ATR":
            fig.add_trace(go.Scatter(x=data.index,y=data['ATR'],line=dict(color='black'),name="ATR", showlegend=True))
        # ---------------- Kalman Filters ----------------
        elif plot_type == "Kalman F":
            fig.add_trace(go.Candlestick(x=data.index,open=data['OpenE'],high=data['HighE'],
                                         low=data['LowE'],close=data['CloseE'],
                                         increasing=dict(line=dict(color="blue")),
                                         decreasing=dict(line=dict(color="orange")),
                                         name="Kalman Filter", showlegend=True))
        elif plot_type == "Kalman E":
            d = data.tail(3)
            fig.add_trace(go.Candlestick(x=d.index,open=d['OpenE'],high=d['HighE'],
                                         low=d['LowE'],close=d['CloseE'],
                                         increasing=dict(line=dict(color="blue")),
                                         decreasing=dict(line=dict(color="orange")),
                                         name="Kalman last 3", showlegend=True))
        # ---------------- MACD ----------------
        elif plot_type == "MACD":
            fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='black', width=1), name="MACD"))
            fig.add_trace(go.Scatter(x=data.index, y=data['SignalMACD'], line=dict(color='#90EE90', width=1), name="Signal MACD"))
            # Histograma MACD (positivos verde / negativos rojo)
            macd_pos = 6*(data['MACD'] - data['SignalMACD']).clip(lower=0)
            macd_neg = 6*(data['MACD'] - data['SignalMACD']).clip(upper=0)
            fig.add_trace(go.Bar(x=data.index, y=macd_pos, marker_color='green', name='Buy Volume', showlegend=True))
            fig.add_trace(go.Bar(x=data.index, y=macd_neg, marker_color='red', name='Sell Volume', showlegend=True))
            # Señales Buy / Sell MACD
            fig.add_trace(go.Scatter(x=data[data['PosicionMACD']==1].index,y=data['MACD'][data['PosicionMACD']==1],
                                    mode='markers', marker=dict(size=15,color='lime',symbol='star-triangle-up'),
                                    name="MACD Buy", showlegend=True))
            fig.add_trace(go.Scatter(x=data[data['PosicionMACD']==-1].index,y=data['MACD'][data['PosicionMACD']==-1],
                                    mode='markers', marker=dict(size=15,color='red',symbol='star-triangle-down'),
                                    name="MACD Sell", showlegend=True))
        # ---------------- Stochastic ----------------
        elif plot_type == "Stochastic":
            fig.add_trace(go.Scatter(x=data.index,y=data['STK'], line=dict(color='brown'), name='Fast %K', showlegend=True))
            fig.add_trace(go.Scatter(x=data.index,y=data['STD'], line=dict(color='black'), name='Fast %D', showlegend=True))
            fig.add_trace(go.Scatter(x=data.index,y=data['STKs'], line=dict(color='#F30000'), name='Slow %K', showlegend=True))
            fig.add_trace(go.Scatter(x=data.index,y=data['STDs'], line=dict(color='#00309E'), name='Slow %D', showlegend=True))
            # Bandas overbought/oversold
            fig.add_trace(go.Scatter(x=data.index,y=[80]*len(data), line=dict(color='red',dash='dash'), name='Overbought',showlegend=True))
            fig.add_trace(go.Scatter(x=data.index,y=[20]*len(data), line=dict(color='blue',dash='dash'), name='Oversold',showlegend=True))
            # Señales filtradas
            buyF  = (data['PosicionSTK']==1)   & (data['STK']<20)
            sellF = (data['PosicionSTK']==-1)  & (data['STD']>80)
            buyS  = (data['PosicionSTKs']==1)  & (data['STKs']<20)
            sellS = (data['PosicionSTKs']==-1) & (data['STDs']>80)
            fig.add_trace(go.Scatter(x=data.index[buyF], y=data['STK'][buyF],
                                     mode='markers',marker=dict(size=15,color="lime",symbol='star-triangle-up'), name='Buy Fast',showlegend=True))
            fig.add_trace(go.Scatter(x=data.index[sellF],y=data['STD'][sellF],
                                     mode='markers',marker=dict(size=15,color="red",symbol='star-triangle-down'), name='Sell Fast', showlegend=True))
            fig.add_trace(go.Scatter(x=data.index[buyS],y=data['STKs'][buyS],
                                     mode='markers',marker=dict(size=15,color="#026B02",symbol='star-triangle-up'), name='Buy',showlegend=True))
            fig.add_trace(go.Scatter(x=data.index[sellS],y=data['STDs'][sellS],
                                     mode='markers',marker=dict(size=15,color="#480000",symbol='star-triangle-down'), name='Sell', showlegend=True))
        # ---------------- Trending ----------------
        elif plot_type == "Trending":
            fig.add_trace(go.Scatter(x=data.index, y=data["FullTrend"], mode="lines", name="Full Trend", line=dict(color="blue", width=2)))
            trend_pack = summary.get("TrendSignals", {})
            levels     = trend_pack.get("levels", {})
            last_value = trend_pack.get("last_value", None)
            signal     = trend_pack.get("signal", "NEUTRAL")

            level_defs = [("strong_buy",  "Strong Bull", "#00B050"),  # Verde fuerte
                          ("buy",         "Weak Bull",   "#92D050"),  # Verde claro
                          ("sell",        "Weak Bear",   "#FFC000"),  # Naranja/Amarillo
                          ("strong_sell", "Strong Bear", "#C00000")]  # Rojo fuerte
            
            # Para dibujar líneas horizontales como TRACES (sí salen en leyenda)
            x0, x1 = data.index[0], data.index[-1]
            for key, label, col in level_defs:
                lvl = levels.get(key)
                if lvl is None:
                    continue
                fig.add_trace(go.Scatter(x=[x0, x1],y=[lvl, lvl],mode="lines",name=label,
                                         line=dict(color=col, width=1, dash="dash"),hoverinfo="skip"))
            if last_value is not None:
                sig_color = ("#00B050" if "BUY" in signal else "#C00000" if "SELL" in signal else "gray")
                fig.add_trace(go.Scatter(x=[x1], y=[last_value], mode="markers", name=f"Signal: {signal}",
                                         marker=dict(size=12, color=sig_color, symbol="diamond"),
                                         hovertemplate=f"Signal: {signal}<br>Value: {last_value:.4f}<extra></extra>"))
            # Leyenda a la derecha y espacio
            fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top", bgcolor="rgba(255,255,255,0)"),margin=dict(r=190))
        # ---------------- H&S + Pennants ----------------
        elif plot_type == "H&S":   
            legend_shown = set()
            def show_once(key):
                if key in legend_shown:
                    return False
                legend_shown.add(key)
                return True
            fig.add_trace(go.Candlestick(x=data.index, open=data['open'], high=data['high'], low=data['low'], close=data['close'], name="Market", showlegend=True))
            # ---------- H&S ----------
            n = len(data)
            for k, p in enumerate(P.get("HCH", []), start=1):
                if ("x" not in p or "y" not in p):
                    continue

                valid_pos = [kk for kk, i in enumerate(p["x"]) if 0 <= i < n and kk < len(p["y"]) and not pd.isna(p["y"][kk])]
                if len(valid_pos) < 2:
                    continue

                X  = [data.index[p["x"][kk]] for kk in valid_pos]
                Y  = [p["y"][kk] for kk in valid_pos]

                fig.add_trace(go.Scatter(x=X, y=Y, mode="lines+markers", line=dict(color="red", width=2),
                                        name="H&S", legendgroup="H&S", showlegend=show_once("H&S"), customdata=[k]*len(X)))

                if p.get("neckline") and p.get("neck_x") and len(p["neck_x"]) == 2 and not any(pd.isna(p["neckline"])):
                    if 0 <= p["neck_x"][0] < n and 0 <= p["neck_x"][1] < n:
                        NX = [data.index[p["neck_x"][0]], data.index[p["neck_x"][1]]]
                        fig.add_trace(go.Scatter(x=NX, y=p["neckline"], mode="lines", line=dict(color="red", dash="dash"),
                                                name="Neckline (H&S)", legendgroup="H&S", showlegend=False))

                # Entry SELL
                if "entry_x" in p and "entry_y" in p and 0 <= p["entry_x"] < n and not pd.isna(p["entry_y"]):
                    fig.add_trace(go.Scatter(x=[data.index[p["entry_x"]]], y=[p["entry_y"]], mode="markers+text", text=["Entry Sell"], textposition="top center",
                                            marker=dict(size=9, color="red"), name="Entry Sell", legendgroup="Entry Sell", showlegend=show_once("Entry Sell")))
            # ---------- H&S Invertido ----------
            n = len(data)
            for k, p in enumerate(P.get("HCHi", []), start=1):
                if ("x" not in p or "y" not in p):
                    continue

                valid_pos = [kk for kk, i in enumerate(p["x"]) if 0 <= i < n and kk < len(p["y"]) and not pd.isna(p["y"][kk])]
                if len(valid_pos) < 2:
                    continue

                X  = [data.index[p["x"][kk]] for kk in valid_pos]
                Y  = [p["y"][kk] for kk in valid_pos]

                fig.add_trace(go.Scatter(x=X, y=Y, mode="lines+markers", line=dict(color="lime", width=2),
                                        name="H&S Inverse", legendgroup="H&S Inverse", showlegend=show_once("H&S Inverse")))
                if p.get("neckline") and p.get("neck_x") and len(p["neck_x"]) == 2 and not any(pd.isna(p["neckline"])):
                    if 0 <= p["neck_x"][0] < n and 0 <= p["neck_x"][1] < n:
                        NX = [data.index[p["neck_x"][0]], data.index[p["neck_x"][1]]]
                        fig.add_trace(go.Scatter(x=NX, y=p["neckline"], mode="lines", line=dict(color="lime", dash="dash"),
                                                name="Neckline (H&S Inverse)", legendgroup="H&S Inverse", showlegend=False))
                # Entry BUY
                if "entry_x" in p and "entry_y" in p and 0 <= p["entry_x"] < n and not pd.isna(p["entry_y"]):
                    fig.add_trace(go.Scatter(x=[data.index[p["entry_x"]]], y=[p["entry_y"]], mode="markers+text", text=["Entry Buy"], textposition="top center",
                                            marker=dict(size=9, color="lime"), name="Entry Buy", legendgroup="Entry Buy", showlegend=show_once("Entry Buy")))
            # ---------- Pennants ----------
            n = len(data)
            for pn in P.get("Pennants", []):
                upper_pos = [k for k, i in enumerate(pn.get("upper_x", [])) if 0 <= i < n and k < len(pn.get("upper_y", [])) and not pd.isna(pn["upper_y"][k])]
                lower_pos = [k for k, i in enumerate(pn.get("lower_x", [])) if 0 <= i < n and k < len(pn.get("lower_y", [])) and not pd.isna(pn["lower_y"][k])]

                UX = [data.index[pn["upper_x"][k]] for k in upper_pos]
                UY = [pn["upper_y"][k] for k in upper_pos]

                LX = [data.index[pn["lower_x"][k]] for k in lower_pos]
                LY = [pn["lower_y"][k] for k in lower_pos]

                if len(UX) >= 2 and len(UY) >= 2:
                    fig.add_trace(go.Scatter(x=UX, y=UY, mode="lines", line=dict(color="orange"), name="Pennant", legendgroup="Pennant",
                                            showlegend=show_once("Pennant")))
                if len(LX) >= 2 and len(LY) >= 2:
                    fig.add_trace(go.Scatter(x=LX, y=LY, mode="lines", line=dict(color="orange"),
                                            name="Pennant (lower)", legendgroup="Pennant", showlegend=False))

                if "pivot" in pn and isinstance(pn["pivot"], dict) and "y" in pn["pivot"]:
                    if "index" in pn and 0 <= pn["index"] < n and not pd.isna(pn["pivot"]["y"]):
                        fig.add_trace(go.Scatter(x=[data.index[pn["index"]]], y=[pn["pivot"]["y"]], mode="markers", marker=dict(size=9, color="orange"),
                                                name="Pennant pivot", legendgroup="Pennant", showlegend=False))

                if "entry_x" in pn and "entry_y" in pn and 0 <= pn["entry_x"] < n and not pd.isna(pn["entry_y"]):
                    side = str(pn.get("side", "BUY")).upper()  # "BUY" / "SELL"
                    if side == "SELL":
                        fig.add_trace(go.Scatter(x=[data.index[pn["entry_x"]]], y=[pn["entry_y"]], mode="markers+text", text=["Entry Sell"], textposition="top center",
                                                marker=dict(size=9, color="red"), name="Entry Sell", legendgroup="Entry Sell", showlegend=show_once("Entry Sell")))
                    else:
                        fig.add_trace(go.Scatter(x=[data.index[pn["entry_x"]]], y=[pn["entry_y"]], mode="markers+text", text=["Entry Buy"], textposition="top center",
                                                marker=dict(size=9, color="lime"), name="Entry Buy", legendgroup="Entry Buy", showlegend=show_once("Entry Buy")))

        fig.update_layout(height=800,title=f"{plot_type}: {asset}")
        fig.update_xaxes(rangeslider_visible=False)
        return fig
