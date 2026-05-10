# =====================================================
# 🧠 IAIngestUtils
# =====================================================
# - Vigila respuestas IA externas
# - Valida hash activo
# - Valida esquema
# - Normaliza SL / TP
# - Ingresa SOLO respuestas válidas al sistema
# =====================================================

import os
from typing                     import Optional
from Chatbot.Cores.project_path import ProjectPaths

class IAIngestUtils:
    REQUIRED_KEYS = {"ia_id", "zip_sha256", "trend", "confidence", "trade_allowed", "sl", "tp"}
    def __init__(self, paths):
        # ✅ Soporta ambos: string root_dir o ProjectPaths
        if isinstance(paths, ProjectPaths):
            self.paths = paths
        else:
            self.paths = ProjectPaths(paths)

        self.root_dir = self.paths.ROOT_DIR  # por si lo usas en logs

        # --- aquí deja lo demás igual pero usando self.paths ---
        self.DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
        self.DEST_DIR     = self.paths.ia_feedback_dir()
        os.makedirs(self.DEST_DIR, exist_ok=True)

        print(f"👁️ [IAIngest] Observando: {self.DOWNLOAD_DIR}")
        print(f"📥 [IAIngest] Destino IA_Feedback: {self.DEST_DIR}")

    # -------------------------------------------------
    # 🔐 Estado actual del sistema
    # -------------------------------------------------
    def _current_zip_hash(self) -> Optional[str]:
        status = self.paths.manage_json(self.paths.chatbot_status_file(), mode="read", default={})
        return status.get("zip_sha256")

    # -------------------------------------------------
    # 🧠 Validaciones
    # -------------------------------------------------
    @classmethod
    def _validate_schema(cls, data) -> bool:
        return cls.REQUIRED_KEYS.issubset(data.keys())

    @staticmethod
    def _normalize_sl_tp(data) -> dict:
        """
        Regla dura:
        - trade_allowed == False → SL = TP = 0
        - trade_allowed == True → SL y TP > 0
        """
        if not bool(data.get("trade_allowed")):
            data["sl"] = 0
            data["tp"] = 0
            return data
        sl = data.get("sl")
        tp = data.get("tp")
        if not isinstance(sl, (int, float)) or sl <= 0:
            raise ValueError("SL inválido con trade_allowed=True")
        if not isinstance(tp, (int, float)) or tp <= 0:
            raise ValueError("TP inválido con trade_allowed=True")
        return data
    # -------------------------------------------------
    # 🚦 run
    # -------------------------------------------------
    def run(self):
        processed = 0
        if not os.path.exists(self.downloads_dir):
            return 0
        for fname in os.listdir(self.downloads_dir):
            if not fname.startswith("IA_Response_") or not fname.endswith(".json"):
                continue
            src = os.path.join(self.downloads_dir, fname)
            try:
                data = self.paths.manage_json(src, mode="read", default={})
                if not self._validate_schema(data):
                    continue
                current_hash = self._current_zip_hash()
                if not current_hash:
                    continue
                if data["zip_sha256"] != current_hash:
                    continue
                data = self._normalize_sl_tp(data)
                ia_dir = self.paths.ia_feedback_dir()
                os.makedirs(ia_dir, exist_ok=True)
                self.paths.manage_json(filepath=self.paths.ia_feedback_file(fname),mode="write",data=data)
                os.remove(src)
                print("🟢 [IAIngest] Respuesta IA aceptada:", fname)
                processed += 1
            except Exception as e:
                print("⚠️ [IAIngest] Error:", fname, e)
        return processed