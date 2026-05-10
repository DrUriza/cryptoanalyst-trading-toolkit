import os
from dash   import html

class MLManager:
    def __init__(self, pred_dir, paths):
        self.pred_dir    = os.path.abspath(pred_dir)
        self.results_dir = os.path.join(self.pred_dir, "Results")
        os.makedirs(self.results_dir, exist_ok=True)
        self.paths       = paths
    def _load_pred(self, timeframe):
        fname   = f"Pred_{timeframe}s.json"
        fpath   = os.path.join(self.results_dir, fname)
        default = { "timeframe": timeframe,
                    "results": {},
                    "meta": {"generated_by": "HMI",
                            "status": "empty",
                            "message": "No prediction data available."}}
        return self.paths.manage_json(fpath, "read", default=default)

    # --------- CFG de ML ----------
    def update_cfg(self, selected_models, action, train_interval, pause_between_intervals, pause_between_cycles):
        try:
            cfg = {"train_interval": int(train_interval),
                   "pause_between_intervals": int(pause_between_intervals),
                   "pause_between_cycles": int(pause_between_cycles),
                   "selected_models": selected_models,
                   "Action": action}
            self.paths.save_cfg(2, cfg)
            print(f"[MLManager] ✅ cfg_1.json updated.")
            return True
        except Exception as e:
            print(f"[MLManager] ❌ Updating Error cfg_1.json: {e}")
            return False

    def generate_ml_table(self, timeframe):
        data = self._load_pred(timeframe)
        if not data or "results" not in data:
            return html.Div(f"No data for {timeframe}s")
        results      = data["results"]
        rows         = []
        label_colors = {"UP": "green", "DOWN": "red", "LATERAL": "orange"}
        for model, info in results.items():
            if "error" in info:
                rows.append(html.Tr([
                    html.Td(model, style={"fontWeight": "bold", "fontSize": "12px"}),
                    html.Td(html.Span(info["error"],
                        style={"color": "red", "fontSize": "12px", "fontStyle": "italic"}), colSpan=2)]))
                continue
            pred_label = info.get("label", "?")
            color      = label_colors.get(pred_label, "gray")
            proba      = info.get("proba", [0, 0, 0])
            pred_cell  = html.Span(pred_label, style={"color": color, "fontWeight": "bold", "fontSize": "12px"})
            proba_cell = html.Span(f"↑ {proba[2]*100:.1f}% | → {proba[1]*100:.1f}% | ↓ {proba[0]*100:.1f}%",
                                   style={"fontSize": "11px", "color": "#555"})
            rows.append(html.Tr([html.Td(model,     style={"fontWeight": "bold", "fontSize": "12px"}),
                                 html.Td(pred_cell, style={"textAlign": "center"}),
                                 html.Td(proba_cell,style={"textAlign": "center"})]))
        title = f"IA {timeframe}s"
        table = html.Table([html.Tr([html.Th(title, colSpan=3)])] + rows,
                           style={"fontSize": "12px", "margin": "10px", "borderSpacing": "6px", "border": "1px solid #ccc", "minWidth": "280px"})
        return table
    # --------- Descubrir modelos disponibles ----------
    def get_available_models(self, representative_tf="60"):
        return [
            # Machine Learning clásico
            "RandomForest", "GradientBoosting", "XGBoost", "LightGBM",
            "SVM", "KNN", "LogisticRegression",
            # Redes neuronales
            "ANN", "DeepLearning", "LSTM", "BiLSTM", "GRU", "CNN1D",
            # Modelos híbridos
            "KalmanRegressor", "KalmanNN", "HybridRF_LSTM",
            # KMeans y GaussianMixture
            "KMeansCluster", "GaussianMixture",
            # Más modelos futuros
            "Transformer", "TemporalFusionTransformer"]
