# =====================================================
# ModelEvaluator.py (final Windows/Linux compatible)
# =====================================================
import os
import json
import joblib
import pandas           as pd
from sklearn.metrics    import classification_report, confusion_matrix, accuracy_score
from concurrent.futures import ProcessPoolExecutor, as_completed


# Función picklable
def _evaluate_one(interval, model_name, paths):
    """Evalúa un modelo en su dataset correspondiente."""
    model_path   = paths.model_file(model_name, interval)
    dataset_path = paths.dataset_path(interval)

    if not os.path.exists(model_path):
        print(f"[WARN] No existe modelo {model_name} para {interval}s")
        return None

    if not os.path.exists(dataset_path):
        print(f"[WARN] No existe dataset para {interval}s → {dataset_path}")
        return None

    df = pd.read_json(dataset_path)
    if "target_bin" not in df.columns:
        print(f"[ERROR] Dataset {dataset_path} no contiene columna 'target_bin'")
        return None

    X = df.drop(columns=["target_bin"])
    y = df["target_bin"]

    try:
        clf = joblib.load(model_path)
        y_pred = clf.predict(X)
    except Exception as e:
        print(f"[ERROR] Evaluando {model_name}: {e}")
        return None

    acc    = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, output_dict=True)
    cm     = confusion_matrix(y, y_pred).tolist()

    folder = os.path.join(paths.REPORTS_DIR, model_name)
    os.makedirs(folder, exist_ok=True)
    report_file = os.path.join(folder, f"Evaluation_{model_name}_{interval}s.json")
    with open(report_file, "w") as f:
        json.dump({
            "interval": interval,
            "model": model_name,
            "accuracy": acc,
            "classification_report": report,
            "confusion_matrix": cm
        }, f, indent=4)

    print(f"[EVAL] {model_name} {interval}s - Accuracy={acc:.3f}")
    return {"accuracy": acc, "report": report, "confusion_matrix": cm}


class ModelEvaluator:
    def __init__(self, interval, paths, models):
        self.interval = interval
        self.paths    = paths
        self.models   = models

    def evaluate(self, model_list):
        if isinstance(model_list, str):
            model_list = [model_list]
        results = {}

        if len(model_list) > 1:
            with ProcessPoolExecutor(max_workers=min(len(model_list), os.cpu_count())) as executor:
                futures = {
                    executor.submit(_evaluate_one, self.interval, m, self.paths): m
                    for m in model_list
                }
                for future in as_completed(futures):
                    model_name = futures[future]
                    results[model_name] = future.result()
        else:
            m = model_list[0]
            results[m] = _evaluate_one(self.interval, m, self.paths)

        return results
