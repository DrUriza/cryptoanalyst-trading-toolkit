# =====================================================
# 📦 ZipCreator - ChatBot Context Builder (PURO + HASH)
# =====================================================
# Responsabilidad ÚNICA:
# - Construir ZIP de contexto
# - Calcular SHA256 del ZIP
# =====================================================
import os
import zipfile
import datetime
from Chatbot.Utilities.hash import HashUtils

class ZipCreator:
    def __init__(self, paths, output_dir=None):
        self.paths = paths
        self.OUTPUT_DIR = output_dir or self.paths.CHATBOT_DIR
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        print(f"📦 [ZIP] ROOT = {self.paths.ROOT_DIR}")
        print(f"📦 [ZIP] OUTPUT_DIR = {self.OUTPUT_DIR}")
    # =================================================
    # Utils
    # =================================================
    def _safe_add(self, zipf, filepath, arcname):
        if os.path.exists(filepath):
            zipf.write(filepath, arcname)
            print(f"➕ ZIP | {arcname}")
        else:
            print(f"⚠️ ZIP | Archivo no encontrado: {filepath}")
    def _add_folder(self, zipf, folder, arc_prefix):
        if not os.path.exists(folder):
            print(f"⚠️ ZIP | Carpeta no encontrada: {folder}")
            return
        for root, _, files in os.walk(folder):
            for f in files:
                if f.endswith(".json"):
                    full = os.path.join(root, f)
                    arc = os.path.join(arc_prefix, f) if arc_prefix else f 
                    zipf.write(full, arc)
                    print(f"➕ ZIP | {arc}")
    # =================================================
    # ZIP Principal
    # =================================================
    def build_zip(self, tfs=(60, 120, 300, 900)):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name  = f"ChatBot_Context_{timestamp}.zip"
        zip_path  = os.path.join(self.OUTPUT_DIR, zip_name)
        print(f"\n📦 Creando ZIP ChatBot → {zip_path}\n")
        # -------------------------
        # 1️⃣ Crear ZIP
        # -------------------------
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # MARKET DATA / PROCESS DATA / SUMMARY DATA / MASTER DATA / ML
            for tf in tfs:
                self._safe_add(zipf, self.paths.market_file(tf),  f"market_data/Market_Data_{tf}s.json")
                self._safe_add(zipf, self.paths.process_file(tf), f"process_data/Process_Data_{tf}s.json")
                self._safe_add(zipf, self.paths.summary_file(tf), f"summary_data/Summary_Data_{tf}s.json")    
                self._safe_add(zipf, self.paths.master_file(tf),  f"master_data/Master_Data_{tf}s.json")
                self._safe_add(zipf, self.paths.rv_file(tf),      f"redval_result/Files/MLReady_{tf}s.json")
                self._safe_add(zipf, self.paths.rv_report(tf),    f"redval_result/Reports/Validation_{tf}s.json")
              # OrderBook
            self._safe_add(zipf, self.paths.orderbook_flat_file(), "orderbook_data/OrderBook_Flat.json")
            self._safe_add(zipf, self.paths.orderbook_metr_file(), "orderbook_data/OrderBook_Metrics.json")
            self._safe_add(zipf, self.paths.orderbook_stat_file(), "orderbook_data/OrderBook_States.json")
        # -------------------------
        # 2️⃣ HASH DEL ZIP (SELLADO)
        # -------------------------
        zip_sha256 = HashUtils.sha256_file(zip_path)
        print(f"🔐 ZIP SHA256 → {zip_sha256}")
        print("\n🟢 ZIP ChatBot creado correctamente (ZIP + HASH)\n")
        return zip_path, zip_sha256
