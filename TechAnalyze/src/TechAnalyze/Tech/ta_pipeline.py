# =====================================================
# Tech/ta_pipeline.py
# =====================================================
import json
import pandas                     as pd
from ..Tech.Indicators.trend      import *
from ..Tech.Indicators.momentum   import *
from ..Tech.Indicators.volatility import *
from ..Tech.Patterns.candles      import *
from ..Tech.Analyzers.regression  import *
from ..Tech.Analyzers.kalman      import *
from ..Tech.Analyzers.topology    import *
from ..Tech.Signals.helpers       import *
from ..Tech.Signals.risk          import *
from .TAResume.tar_pipeline       import *
from .Orderbook.ob_pipeline       import *

class TechAnalyzePipeline:
    def __init__(self, paths):
        self.paths = paths  
        self.alpha = 0.6
        self._ob_prev = {} 
    def run_analysis(self, interval,cycle=0):
        try:
            if cycle==0:
                # ================== LOAD MARKET ==================
                path1     = self.paths.market_file(interval)
                data      = pd.DataFrame(self.paths.manage_json(filepath=path1, mode="read", default=[]))
                path2     = self.paths.orderbook_flat_file()
                ob_fla    = pd.DataFrame(self.paths.manage_json(filepath=path2, mode="read", default={}))
                path3     = self.paths.orderbook_metric_file()
                path4     = self.paths.orderbook_states_file()
                ob_sta    = pd.DataFrame(self.paths.manage_json(filepath=path4, mode="read", default={}))
                out_path1 = self.paths.process_file(interval)
                out_path2 = self.paths.summary_file(interval)
                # ================== INDICADORES ==================
                data['RSI'], data['TSI'], data['PosicionRSI'], data['PosicionTSI'] = RSI_TSI(data)
                data['STK'], data['STD'], data['PosicionSTK']    = Stochastic_OscillatorFast(data)
                data['STKs'], data['STDs'], data['PosicionSTKs'] = Stochastic_OscillatorSlow(data)
                data['ATR'] = ATR(data)
                data['y_pred'], data['OptimalDegree'] = Regressor(data)
                data['BB-A'], data['BB-B'], data['BB-M'], data['PosicionBB-R'] = BB(data)
                data['ADX'], data['MD+'], data['MD-'], data['PosicionADX'] = ADX(data)
                data['OpenE'], data['CloseE'], data['LowE'], data['HighE'] = Kalman_Filter(data)
                data['WD'], data['PosicionWD'] = Wasserstein_Distances(data)
                data['MA-S-S'], data['MA-S-L'], data['PosicionMM-S'], data['MA-S'] = SMM(data)
                data['MA-E-S'], data['MA-E-L'], data['PosicionMM-E'], shortE, longE, data['MA-E'] = EMM(data)
                data['MA-S'], data['MA-L'], data['PosicionMM-N'], data['MA-N'] = WMM(data)
                data['MACD'], data['SignalMACD'], data['PosicionMACD']         = MACDMM(data, shortE, longE)
                data['StopLoss'], data['TakeProfit'] = StopLoss_TakeProfit(data)
                data["Candles"]   = classify_candle(data)
                data['TrendA']    = TrendA(data)
                data['TrendB']    = TrendB(data)
                data["FullTrend"] = (data['TrendA']*self.alpha + data['TrendB']*(1-self.alpha))*10
                data['Color']     = data["FullTrend"].map({1: "green", -1: "red", 0: "gray"}).fillna("gray")
                # ================== FUSIÓN FINAL ==================
                ta_resume = techtable(data)
                # ================== High Volume ==================
                high_vol  = high_volume(data)
                # ================== PATTERNS (POST-FUSION) ==================
                hs = build_hs_struct(data)
                patterns = {"HCH": hs.get("HCH"),"HCHi": hs.get("HCHi"),"Fibo": build_fibo_struct(data),"SR": build_sr_struct(data),"Pennants": build_pennants_struct(data)}
                # ================== OrderBook ==================
                prev = self._ob_prev.get(interval, {})
                prev_ob_fla = prev.get("ob_fla")
                prev_metrics = prev.get("metrics")
                ob_metrics, ob_deltas, ob_pull, ob_states = orderbook_pipeline(ob_fla, ob_sta,prev_ob_fla=prev_ob_fla,prev_metrics=prev_metrics,max_levels=2)
                # ================== Trendsignals ==================
                trend_sig = build_trending_struct(data)
                # ================== Resume ==================
                summary = {"TA_Resume": ta_resume, "High_Volume": high_vol, "Patterns": patterns, "TrendSignals":trend_sig}
                # ================== SAVE ==================
                ob_metrics_out = {**ob_metrics, **ob_deltas, **ob_pull}
                self.paths.manage_json(filepath=path3, mode="write", data=ob_metrics_out)
                self.paths.manage_json(filepath=path4, mode="write", data=ob_states)
                self.paths.manage_json(filepath=out_path1, mode="write", data=json.loads(data.to_json(orient="records")))
                self.paths.manage_json(filepath=out_path2, mode="write", data=summary)
                self._ob_prev[interval] = {"ob_fla": ob_fla.copy(), "metrics": ob_metrics}
                print(f"💾 [Process] Guardado → {out_path1}")
                print(f"💾 [Summary] Guardado → {out_path2}")
            else:
                # ================== LOAD MARKET ==================
                path2     = self.paths.orderbook_flat_file()
                ob_fla    = pd.DataFrame(self.paths.manage_json(filepath=path2, mode="read", default={}))
                path3     = self.paths.orderbook_metric_file()
                path4     = self.paths.orderbook_states_file()
                ob_sta    = pd.DataFrame(self.paths.manage_json(filepath=path4, mode="read", default={}))
                # ================== OrderBook ==================
                prev = self._ob_prev.get(interval, {})
                prev_ob_fla = prev.get("ob_fla")
                prev_metrics = prev.get("metrics")
                ob_metrics, ob_deltas, ob_pull, ob_states = orderbook_pipeline(ob_fla, ob_sta,prev_ob_fla=prev_ob_fla,prev_metrics=prev_metrics,max_levels=2)
                # ================== SAVE ==================
                ob_metrics_out = {**ob_metrics, **ob_deltas, **ob_pull}
                self.paths.manage_json(filepath=path3, mode="write", data=ob_metrics_out)
                self.paths.manage_json(filepath=path4, mode="write", data=ob_states)
                self._ob_prev[interval] = {"ob_fla": ob_fla.copy(), "metrics": ob_metrics}
                print(f"🟢 OrderBook Listo [{interval}s]")
        except Exception as e:
            print(f"❌ [ERROR][Analyze][{interval}s] {e}")
