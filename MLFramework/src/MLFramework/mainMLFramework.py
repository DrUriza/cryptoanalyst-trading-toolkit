# =====================================================
# mainMLFramework.py (versión limpia final)
# =====================================================
# Autor: Ottmar Uriza
# Descripción:
#   MLFramework ejecuta entrenamiento, evaluación y
#   predicción SOLO para los intervals recibidos desde
#   Prueba.py o eLatinApp.
#
#   cfg_2.json SOLO controla modelos y parámetros,
#   NO intervalos.
# =====================================================

import os
import json
import datetime
import warnings
import shutil
import time

from sklearn.exceptions import ConvergenceWarning, UndefinedMetricWarning
from .BinaryDecisions   import ModelTrainer, ModelEvaluator, ModelPredictor, ModelRegistry
from .Cores             import ProjectPaths

# --- Silenciar warnings ---
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UndefinedMetricWarning)

# =====================================================
# Clase principal
# =====================================================
class MLFrameworkApp:
    def __init__(self, root_dir, debug=True):
        self.root_dir = os.path.abspath(root_dir)
        self.paths    = ProjectPaths(self.root_dir)
        self.debug    = debug
        self.registry = ModelRegistry()
        print(f"🟢 MLFrameworkApp inicializado en: {self.root_dir}")
        self.clean_cache()
    # -----------------------------------------------
    def log(self, msg):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}][MLFrameworkApp] {msg}")
    # =====================================================
    # Limpieza robusta (con FIX para evitar errores Windows)
    # =====================================================
    def clean_cache(self):
        """
        Limpieza optimizada y segura:
        - SOLO limpia __pycache__ una vez por ejecución
        - NO entra en la carpeta Trash (evita loops)
        - Elimina archivos basura (.tmp, .log, .bak, json corruptos)
        - No intenta limpiar lo que Python vuelva a generar durante la ejecución
        """
        base_dir  = self.root_dir
        trash_dir = os.path.join(base_dir, "Trash")
        os.makedirs(trash_dir, exist_ok=True)

        suspicious_exts  = (".tmp", ".temp", ".log", ".bak", ".partial", ".incomplete")
        suspicious_names = (".DS_Store", "Thumbs.db")
        now_stamp        = time.strftime("%Y%m%d_%H%M%S")

        print("[CLEAN] Limpieza optimizada iniciada...")

        for root, dirs, files in os.walk(base_dir):

            # -------------------------------------------
            # 1) NUNCA entrar a Trash (evita ciclos)
            # -------------------------------------------
            if trash_dir in os.path.abspath(root):
                continue

            # -------------------------------------------
            # 2) Limpiar carpetas __pycache__
            # -------------------------------------------
            for d in list(dirs):
                if d == "__pycache__":
                    src = os.path.join(root, d)
                    dst = os.path.join(trash_dir, f"__pycache___{now_stamp}")
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    try:
                        shutil.move(src, dst)
                        print(f"[CLEAN] Moved __pycache__ → {dst}")
                    except Exception as e:
                        print(f"[CLEAN][WARN] No se pudo mover {src}: {e}")
                    dirs.remove(d)  # Evita recursión

            # -------------------------------------------
            # 3) Limpiar archivos basura
            # -------------------------------------------
            for f in files:
                src = os.path.join(root, f)
                move = False

                # Archivos directamente sospechosos
                if f in suspicious_names or f.endswith(suspicious_exts):
                    move = True

                # JSON corruptos o vacíos
                if f.endswith(".json"):
                    try:
                        if os.path.getsize(src) == 0:
                            move = True
                        else:
                            json.load(open(src, "r", encoding="utf-8"))
                    except:
                        move = True

                if move:
                    dst = os.path.join(trash_dir, f"{f}_{now_stamp}")
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    try:
                        shutil.move(src, dst)
                        print(f"[CLEAN] Moved file → {dst}")
                    except Exception as e:
                        print(f"[CLEAN][WARN] No se pudo mover archivo {src}: {e}")

        print("[CLEAN] Limpieza completada.\n")

    # =====================================================
    # Cargar SOLO modelos desde cfg_2.json
    # =====================================================
    def load_selected_models(self):
        cfg_path = self.paths.CFG_FILE  
        print(f"[DEBUG] Leyendo cfg_2.json desde: {cfg_path}")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            print(f"[DEBUG] Contenido cfg_2.json: {cfg}")
            models = cfg.get("selected_models")
            # Si no existe, está vacío o es lista vacía → usar default
            if not models:
                print("[DEBUG] selected_models vacío → usando defaults")
                return ["RandomForest", "GradientBoosting"]
            return models

        except Exception as e:
            self.log(f"[WARN] Error leyendo cfg_2.json → {e}")
            return ["RandomForest", "GradientBoosting"]

    # =====================================================
    # Ejecuta un ciclo completo para un intervalo
    # =====================================================
    def run_pipeline(self, interval, selected_models):
        dataset_path = self.paths.dataset_path(interval)
        result_file  = self.paths.result_file(interval)
        print(f"[DEBUG] Buscando MLReady en: {dataset_path}")
        if not os.path.exists(dataset_path):
            self.log(f"[SKIP] MLReady_{interval}s.json no encontrado.")
            return
        for model_name in selected_models:
            try:
                self.log(f"[PIPELINE] Entrenando {model_name} @ {interval}s")
                trainer = ModelTrainer(interval, self.paths, self.registry)
                trainer.train_interval([model_name])
                evaluator = ModelEvaluator(interval, self.paths, self.registry)
                evaluator.evaluate([model_name])
                predictor = ModelPredictor(interval, self.paths, self.registry)
                results   = predictor.predict([model_name], dataset_path)
            except Exception as e:
                results = {"error": str(e)}
                self.log(f"[ERROR][{model_name}]: {e}")
            # Guardar resultados
            try:
                json.dump({"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           "interval": interval,
                           "model": model_name,
                           "results": results}, 
                    open(result_file, "w", encoding="utf-8"), indent=4)
                self.log(f"[SAVE] Resultados guardados en {result_file}")
            except Exception as e:
                self.log(f"[ERROR][SAVE] No se pudo guardar resultados: {e}")
    # =====================================================
    # Método principal llamado desde Prueba.py o HMI
    # =====================================================
    def run(self, intervals, models=None):
        selected_models = models if models else self.load_selected_models()
        self.log(f"[RUN] Intervals: {intervals}")
        self.log(f"[RUN] Models: {selected_models}")
        for tf in intervals:
            self.run_pipeline(tf, selected_models)
        self.log("[DONE] MLFramework completado.")
