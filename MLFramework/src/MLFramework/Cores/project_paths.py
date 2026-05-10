# =====================================================
# 🤖 MLFramework - ProjectPaths (versión profesional)
# =====================================================
# Autor: Ottmar Uriza
# Descripción:
#   Gestor central de rutas para la librería MLFramework.
#   Crea automáticamente la estructura interna en /Data,
#   valida cfg_2.json y garantiza independencia.
# =====================================================
import os
import json

class ProjectPaths:
    def __init__(self, root_dir: str):
        """
        root_dir → carpeta raíz del proyecto donde vive /Data.
        Ejemplo:
            C:/ """
        self.ROOT_DIR = os.path.abspath(root_dir)
        # =====================================================
        # 📁 Estructura principal (/Data y subcarpetas)
        # =====================================================
        self.DATA_DIR    = os.path.join(self.ROOT_DIR, "Data")
        self.CFG_DIR     = os.path.join(self.DATA_DIR, "CFG")
        # --- Carpetas específicas del Framework ---
        self.ML_DIR      = os.path.join(self.DATA_DIR, "ML")
        self.MODELS_DIR  = os.path.join(self.ML_DIR, "ML_Models")
        self.REPORTS_DIR = os.path.join(self.ML_DIR, "ML_Reports")
        self.RESULTS_DIR = os.path.join(self.ML_DIR, "Results")
        # --- RedVal Results (input proveniente de TechAnalyze/TA) ---
        self.REDVAL_DIR   = os.path.join(self.DATA_DIR, "RedVal Results")
        self.REDVAL_FILES = os.path.join(self.REDVAL_DIR, "Files")
        # =====================================================
        # 📄 Archivo de configuración de MLFramework (cfg_2)
        # =====================================================
        self.CFG_FILE = os.path.join(self.CFG_DIR, "cfg_2.json")

        # Crear rutas y defaults si falta algo
        self._ensure_dirs()
        self._ensure_cfg()

        print("📁 [MLFramework Paths] Rutas inicializadas correctamente.")

    # =====================================================
    # 🛠 Crear carpetas requeridas
    # =====================================================
    def _ensure_dirs(self):
        folders = [
            self.DATA_DIR,
            self.CFG_DIR,
            self.ML_DIR,
            self.MODELS_DIR,
            self.REPORTS_DIR,
            self.RESULTS_DIR,
            self.REDVAL_DIR,
            self.REDVAL_FILES,
        ]
        for d in folders:
            os.makedirs(d, exist_ok=True)

    # =====================================================
    # 🧩 Crear archivo cfg_2.json si no existe
    # =====================================================
    def _ensure_cfg(self):
        if not os.path.exists(self.CFG_FILE):
            default_cfg = {
                "intervals": [60, 120, 300, 900],
                "selected_models": ["RandomForest", "GradientBoosting"],
                "train_interval": 1800,
                "pause_between_intervals": 5,
                "pause_between_cycles": 10,
                "notes": "cfg_2.json inicial auto-generado por MLFramework."
            }
            with open(self.CFG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_cfg, f, indent=4)
            print(f"💾 [MLFramework] cfg_2.json creado → {self.CFG_FILE}")

    # =====================================================
    # 🔍 Métodos estándar para obtener rutas de archivos
    # =====================================================

    def dataset_path(self, tf: int) -> str:
        """
        📥 Dataset listo para ML:
            MLReady_60s.json, MLReady_120s.json, etc.
        """
        return os.path.join(self.REDVAL_FILES, f"MLReady_{tf}s.json")

    def model_file(self, model_name: str, tf: int) -> str:
        """
        📦 Ruta al modelo entrenado:
            ML_Models/RandomForest_60s.joblib
        """
        clean = model_name.replace(" ", "_")
        return os.path.join(self.MODELS_DIR, f"{clean}_{tf}s.joblib")

    def result_file(self, tf: int) -> str:
        """
        📄 Resultado final de predicción del modelo:
            ML_Results_60s.json
        """
        return os.path.join(self.RESULTS_DIR, f"ML_Results_{tf}s.json")

    def report_file(self, name: str) -> str:
        """
        🖼 Ruta auxiliar para guardar reportes gráficos:
            ML_Reports/<nombre>.png
        """
        return os.path.join(self.REPORTS_DIR, f"{name}.png")
