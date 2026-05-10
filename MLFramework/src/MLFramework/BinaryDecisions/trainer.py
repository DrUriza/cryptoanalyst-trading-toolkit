# =====================================================
# ModelTrainer.py (final Windows/Linux compatible)
# =====================================================
import os
import json
import joblib
import pandas                as pd
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.metrics         import accuracy_score, classification_report, confusion_matrix
from sklearn.ensemble        import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm             import SVC
from sklearn.linear_model    import LogisticRegression
from scipy.stats             import randint, uniform
from concurrent.futures      import ProcessPoolExecutor, as_completed


# =====================================================
# Función global picklable (necesario para Windows)
# =====================================================
def _train_one(interval, model_name, paths, param_spaces, model_dict):
    """Entrena un modelo individual (función global -> picklable)."""
    # === Dataset ===
    path = paths.dataset_path(interval)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset no encontrado: {path}")

    df = pd.read_json(path)
    if "target_bin" not in df.columns:
        raise ValueError(f"El dataset {path} no contiene columna 'target_bin'")

    X = df.drop(columns=["target_bin"]).values
    y = df["target_bin"].values

    # === Validación cruzada temporal ===
    tscv = TimeSeriesSplit(n_splits=5)
    print(f"\n[INFO] Optimizando {model_name} para {interval}s...")

    search = RandomizedSearchCV(
        model_dict[model_name],
        param_distributions=param_spaces[model_name],
        n_iter=20,
        cv=tscv,
        scoring="accuracy",
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    search.fit(X, y)

    best_model = search.best_estimator_

    # === Guardado ===
    model_path = paths.model_file(model_name, interval)
    joblib.dump(best_model, model_path)

    # === Evaluación rápida ===
    y_pred = best_model.predict(X)
    acc = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, output_dict=True)
    cm = confusion_matrix(y, y_pred).tolist()

    # === Guardado de métricas ===
    folder = os.path.join(paths.REPORTS_DIR, model_name)
    os.makedirs(folder, exist_ok=True)
    metrics_file = os.path.join(folder, f"FinalReport_{model_name}_{interval}s.json")
    with open(metrics_file, "w") as f:
        json.dump({
            "interval": interval,
            "model": model_name,
            "best_params": search.best_params_,
            "accuracy": acc,
            "classification_report": report,
            "confusion_matrix": cm
        }, f, indent=4)

    print(f"[RESULT] {model_name} {interval}s - Accuracy={acc:.3f}")
    print(f"[SAVE] Modelo en {model_path}")
    print(f"[SAVE] Reporte en {metrics_file}")
    return model_name, model_path, acc


# =====================================================
# Clase principal
# =====================================================
class ModelTrainer:
    def __init__(self, interval, paths, models):
        self.interval = interval
        self.paths    = paths
        self.models   = models

        # Espacios de hiperparámetros
        self.param_spaces = {
            "RandomForest": {
                "n_estimators": randint(100, 600),
                "max_depth": randint(5, 20),
                "min_samples_split": randint(10, 100),
                "min_samples_leaf": randint(5, 50),
                "max_features": ["sqrt", "log2", None],
                "bootstrap": [True, False]
            },
            "GradientBoosting": {
                "n_estimators": randint(50, 400),
                "learning_rate": uniform(0.01, 0.3),
                "max_depth": randint(3, 10),
                "min_samples_split": randint(2, 50),
                "min_samples_leaf": randint(1, 20)
            },
            "SVM": {
                "C": uniform(0.1, 10),
                "kernel": ["linear", "rbf", "poly"],
                "gamma": ["scale", "auto"]
            },
            "LogisticRegression": {
                "C": uniform(0.1, 10),
                "penalty": ["l2"],
                "solver": ["lbfgs", "saga"],
                "max_iter": [1000]
            }
        }

        # Modelos base
        self.model_dict = {
            "RandomForest":       RandomForestClassifier(random_state=42, n_jobs=-1),
            "GradientBoosting":   GradientBoostingClassifier(random_state=42),
            "SVM":                SVC(probability=True, random_state=42),
            "LogisticRegression": LogisticRegression(random_state=42, n_jobs=-1)
        }

    def train_interval(self, model_list):
        """Entrena uno o más modelos para el intervalo actual."""
        if isinstance(model_list, str):
            model_list = [model_list]
        results = {}

        if len(model_list) > 1:
            with ProcessPoolExecutor(max_workers=min(len(model_list), os.cpu_count())) as executor:
                futures = {
                    executor.submit( _train_one,self.interval, m, self.paths, self.param_spaces, self.model_dict): m for m in model_list}
                for future in as_completed(futures):
                    model_name = futures[future]
                    try:
                        _, model_path, acc = future.result()
                        results[model_name] = {"path": model_path, "accuracy": acc}
                    except Exception as e:
                        print(f"[ERROR] Entrenando {model_name}: {e}")
                        results[model_name] = None
        else:
            m = model_list[0]
            _, model_path, acc = _train_one(self.interval, m, self.paths, self.param_spaces, self.model_dict)
            results[m] = {"path": model_path, "accuracy": acc}

        return results
