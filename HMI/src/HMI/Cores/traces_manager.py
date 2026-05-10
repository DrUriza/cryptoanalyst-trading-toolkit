# =====================================================
# Core/traces_manager.py
# =====================================================
import os
import pandas             as pd
from datetime             import timedelta

class TraceManager:
    def __init__(self, paths):
        self.paths    = paths
        self.cfg_dir  = os.path.abspath(paths.CFG_DIR)
        self.proc_dir = os.path.abspath(paths.PROCESS_DIR)
        self.summ_dir = os.path.abspath(paths.SUMMARY_DIR)

    def _load_json(self, filepath, default):
        if not filepath or not os.path.exists(filepath):
            print(f"[TraceManager] ❌ No existe {filepath}")
            return default
        try:
            return self.paths.manage_json(filepath, mode="read", default=default)
        except Exception as e:
            print(f"[TraceManager] ⚠️ Error leyendo {filepath}: {e}")
            return default

    def load_process_df(self, interval):
        filepath = self.paths.process_file(interval)
        data = self._load_json(filepath, default=[])
        df = pd.DataFrame(data)
        if df.empty:
            return df
        if "timestamp" in df.columns:
            try:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms") - timedelta(hours=6)
                df.set_index("timestamp", inplace=True)
            except Exception as e:
                print("⚠️ error timestamp:", e)
        try:
            df.index = pd.to_datetime(df.index)
        except Exception:
            pass
        return df
    
    def load_summary(self, interval):
        filepath = self.paths.summary_file(interval)
        data = self._load_json(filepath, default={})
        if isinstance(data, list):
            return data[-1] if data else {}
        if isinstance(data, dict):
            return data
        return {}

    # -----------------------------
    # Carga de datos de mercado
    # -----------------------------
    def update_market_data(self, asset, zoom, source):
        print("✅ TraceManager.update_market_data()")
        print(f"   asset={asset}  source={source}  zoom={zoom}")
        # --- Process ---
        data = self.load_process_df(source)
        if data.empty:
            return {"df": pd.DataFrame(), "summary": {}}
        # --- Zoom ---
        size = int(len(data) / max(1, int(zoom)))
        data = data.tail(size)
        # --- Summary ---
        summary = self.load_summary(source)
        if not isinstance(summary, dict):
            summary = {}

        summary.setdefault("TA_Resume", {})
        summary.setdefault("Patterns", {})
        summary.setdefault("TrendSignals", {})
        summary.setdefault("High_Volume", 0)
        return data, summary

