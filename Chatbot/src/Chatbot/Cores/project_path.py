# =====================================================
# 🤖 ProjectPaths ChatBot 
# =====================================================
import os
import json
from .root_finder import GetRoot  

class ProjectPaths:
    def __init__(self, root_dir=None, tag="Chatbot", create_structure=True):
        self.TAG = tag
        print(f"🤖 [{self.TAG}] Inicializando ProjectPaths...")
        # ROOT único (si no lo mandan, aquí se decide)
        if not root_dir:
            root_dir = GetRoot(verbose=True)
        self.ROOT_DIR = os.path.abspath(root_dir)
        print(f"📁 [{self.TAG} Paths] ROOT_DIR = {self.ROOT_DIR}")
        self.DATA_DIR = os.path.join(self.ROOT_DIR, "Data")
        if not os.path.isdir(self.DATA_DIR):
            raise RuntimeError(f"[FATAL PATHS] ROOT inválido, falta Data: {self.DATA_DIR}")
        # === Carpetas ===
        self.DATA_DIR      = os.path.join(self.ROOT_DIR, "Data")
        self.CFG_DIR       = os.path.join(self.DATA_DIR, "CFG")
        self.CFG_FILE1     = os.path.join(self.CFG_DIR, "cfg_1.json")
        self.MARKET_DIR    = os.path.join(self.DATA_DIR, "Market Data")
        self.PROCESS_DIR   = os.path.join(self.DATA_DIR, "Process Data")
        self.SUMMARY_DIR   = os.path.join(self.DATA_DIR, "Summary Data")
        self.ORDERBOOK_DIR = os.path.join(self.DATA_DIR, "OrderBook Data")
        self.MASTER_DIR    = os.path.join(self.DATA_DIR, "Master Data")
        self.ML_DIR        = os.path.join(self.DATA_DIR, "ML")
        self.CHATBOT_DIR   = os.path.join(self.DATA_DIR, "ChatBot_Context")    
        self.REDVAL_DIR    = os.path.join(self.DATA_DIR, "RedVal Results")
        self.RV_FILE       = os.path.join(self.REDVAL_DIR , "Files")
        self.RV_REPORT     = os.path.join(self.REDVAL_DIR , "Reports")
  
        if create_structure:
            self._ensure_dirs()
            self._ensure_cfg()
        print(f"🟢 [{self.TAG}] Directorios y configuraciones listas.\n")
    # -------------------------------------------------
    def _ensure_dirs(self):
        print("🗂️ [ChatBot] Verificando estructura de carpetas...")
        dirs = [self.DATA_DIR,
                self.CFG_DIR,
                self.MARKET_DIR,
                self.PROCESS_DIR,
                self.MASTER_DIR,
                self.SUMMARY_DIR,
                self.REDVAL_DIR,
                self.ML_DIR,
                self.CHATBOT_DIR]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            print(f"📁   → OK: {d}")
    # -------------------------------------------------------------------------------------------------
    def _ensure_cfg(self):
        print("⚙️ [ChatBot] Verificando archivos CFG...")
        if not os.path.exists(self.CFG_FILE1):
            self.manage_json(self.CFG_FILE1,"write",{"asset": "BTCUSD"})
            print(f"🆕 [CFG] Creado cfg_1.json → {self.CFG_FILE1}")
        else:
            print(f"📖 [CFG] cfg_1.json cargado.")
    # -------------------------------------------------------------------------------------------------
    def manage_json(self, filepath, mode="read", data=None, default=None):
        if default is None:
            default = {}
        if mode == "read":
            if not os.path.exists(filepath):
                json.dump(default, open(filepath, "w"), indent=4)
                print(f"🆕 [JSON] Creado default → {filepath}")
                return default
            try:
                print(f"📖 [JSON] Read → {filepath}")
                return json.load(open(filepath, "r"))
            except:
                print(f"⚠️ [WARN] JSON corrupto, usando default → {filepath}")
                return default
        elif mode == "write":
            json.dump(data, open(filepath, "w"), indent=4)
            print(f"💾 [JSON] Saved → {filepath}")
            return True
        else:
            raise ValueError("mode must be 'read' or 'write'")
    # -------------------------------------------------------------------------------------------------
    def market_file(self, tf):         return os.path.join(self.MARKET_DIR,  f"Market_Data_{tf}s.json")
    def process_file(self, tf):        return os.path.join(self.PROCESS_DIR, f"Process_Data_{tf}s.json")
    def summary_file(self, tf):        return os.path.join(self.SUMMARY_DIR, f"Summary_Data_{tf}s.json")
    def master_file(self, tf):         return os.path.join(self.MASTER_DIR,  f"Master_Data_{tf}s.json")
    def rv_report(self, tf):           return os.path.join(self.RV_REPORT,   f"Validation_{tf}s.json")
    def rv_file(self, tf):             return os.path.join(self.RV_FILE,     f"MLReady_{tf}s.json")
    def orderbook_flat_file(self):     return os.path.join(self.ORDERBOOK_DIR, "OrderBook_Flat.json")
    def orderbook_stat_file(self):     return os.path.join(self.ORDERBOOK_DIR, "OrderBook_States.json")
    def orderbook_metr_file(self):     return os.path.join(self.ORDERBOOK_DIR, "OrderBook_Metrics.json")
    def chatbot_question_file(self):   return os.path.join(self.CHATBOT_DIR, "user_question.json")
    def chatbot_prompt_file(self):     return os.path.join(self.CHATBOT_DIR, "chatbot_prompt.json")
    def chatbot_status_file(self):     return os.path.join(self.CHATBOT_DIR, "chatbot_status.json")
    def ia_feedback_dir(self):         return os.path.join(self.DATA_DIR,    "IA_Feedback")
    def ia_feedback_file(self, fname): return os.path.join(self.ia_feedback_dir(), fname)
