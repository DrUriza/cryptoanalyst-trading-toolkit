# =====================================================
# ReductionPipeline - TechAnalyze Framework
# =====================================================
# Autor: Ottmar Uriza
# Descripción:
#  Orquesta reducción de dimensionalidad (correlación + PCA)
#  y validación ML-ready.
# =====================================================
import os
import pandas    as pd
from  .Reducer   import build_master_dataframe, correlation_filter
from  .PCA       import run_pca
from  .Validator import validate_dataframe

class ReductionPipeline:
    def __init__(self, paths, interval, default_atr_factor=1.5):
        self.paths    = paths
        self.interval = interval
        self.default_atr_factor = default_atr_factor
    # -----------------------------
    # Utils
    # -----------------------------
    def _resolve_atr_factor(self, process_df):
        if "ATR" in process_df.columns:
            atr_series = process_df["ATR"].dropna()
            if not atr_series.empty:
                atr_value = atr_series.iloc[-1]
                print(f"📐 [Reduction] ATR detectado → {atr_value:.4f}")
                return atr_value
        print(f"⚠️ [Reduction] ATR no encontrado → usando default {self.default_atr_factor}")
        return self.default_atr_factor

    def _load_json_df(self, filepath):
        data = self.paths.manage_json(filepath=filepath, mode="read", default=[])
        if isinstance(data, dict):
            return pd.DataFrame([data])
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame([])

    def _load_json_dfs(self, *filepaths):
        return tuple(self._load_json_df(fp) for fp in filepaths)

    # -----------------------------
    # Run pipeline
    # -----------------------------
    def run(self):
        print(f"🟣 [Reduction] Procesando @ {self.interval}s")
        # ---------- Paths ----------
        paths = (self.paths.process_file(self.interval),
                 self.paths.summary_file(self.interval),
                 self.paths.orderbook_flat_file(),
                 self.paths.orderbook_metric_file(),
                 self.paths.orderbook_states_file())
        path6 = self.paths.master_file(self.interval)
        # ---------- Loads ----------
        process_df, summary_df, ob_flat, ob_met, ob_sta = self._load_json_dfs(*paths)
        # ---------- ATR factor ----------
        atr_factor = self._resolve_atr_factor(process_df)
        # ---------- Master DF ----------
        df_master = build_master_dataframe(process_df, summary_df, ob_flat, ob_met, ob_sta, atr_factor)
        # ---------- Correlation filter ----------
        df_red = correlation_filter(df_master, name=f"{self.interval}s", threshold=0.95)
        # ---------- PCA ----------
        df_pca = run_pca(df_red, interval=f"{self.interval}s")
        # ---------- Validation ----------
        report, df_ml_ready = validate_dataframe(df_pca, name=f"{self.interval}s")
        # ---------- Persistencia ----------
        self.paths.manage_json(filepath=path6, mode="write", data=df_pca.to_dict(orient="records"))
        if report is not None:
            report_path = os.path.join(self.paths.REDVAL_REPORTS, f"Validation_{self.interval}s.json")
            self.paths.manage_json(filepath=report_path, mode="write", data=report)
        clean_path = os.path.join(self.paths.REDVAL_FILES, f"MLReady_{self.interval}s.json")
        self.paths.manage_json(filepath=clean_path, mode="write", data=df_ml_ready.to_dict(orient="records"))
        print(f"🟣 [Reduction] Completado → {self.interval}s")
