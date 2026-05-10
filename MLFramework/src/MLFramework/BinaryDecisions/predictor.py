# =====================================================
# ModelPredictor.py (final Windows/Linux compatible)
# =====================================================
import os
import joblib
import pandas           as pd
from concurrent.futures import ProcessPoolExecutor, as_completed


# Función picklable
def _predict_one(interval, model_name, paths, latest):
    """Predice una fila con un modelo ya entrenado."""
    model_path = paths.model_file(model_name, interval)
    if not os.path.exists(model_path):
        return {"error": f"Modelo no encontrado: {model_path}"}
    try:
        clf = joblib.load(model_path)
        if hasattr(clf, "n_features_in_") and latest.shape[1] != clf.n_features_in_:
            return {"error": f"El modelo {model_name} fue entrenado con {clf.n_features_in_} features, "
                             f"pero el dataset actual tiene {latest.shape[1]}."}
        pred   = clf.predict(latest)[0]
        label  = {1: "UP", -1: "DOWN", 0: "LATERAL"}.get(pred, str(pred))
        result = {"prediction": int(pred), "label": label}
        if hasattr(clf, "predict_proba"):
            result["proba"] = clf.predict_proba(latest)[0].tolist()
        print(f"[PREDICT] {model_name} {interval}s -> {label}")
        return result
    except Exception as e:
        return {"error": f"Error en predicción con {model_name}: {e}"}


class ModelPredictor:
    def __init__(self, interval, paths, models):
        self.interval = interval
        self.paths    = paths
        self.models   = models

    def predict(self, model_list, file_path):
        if isinstance(model_list, str):
            model_list = [model_list]

        if not os.path.exists(file_path):
            return {"error": f"Archivo no encontrado: {file_path}"}
        try:
            df = pd.read_json(file_path)
            if "target_bin" in df.columns:
                latest = df.drop(columns=["target_bin"]).iloc[-1].values.reshape(1, -1)
            else:
                latest = df.iloc[-1].values.reshape(1, -1)
        except Exception as e:
            return {"error": f"Error leyendo archivo {file_path}: {e}"}

        results = {}
        if len(model_list) > 1:
            with ProcessPoolExecutor(max_workers=min(len(model_list), os.cpu_count())) as executor:
                futures = {
                    executor.submit(_predict_one, self.interval, m, self.paths, latest): m
                    for m in model_list
                }
                for future in as_completed(futures):
                    model_name = futures[future]
                    results[model_name] = future.result()
        else:
            m = model_list[0]
            results[m] = _predict_one(self.interval, m, self.paths, latest)
        return results

