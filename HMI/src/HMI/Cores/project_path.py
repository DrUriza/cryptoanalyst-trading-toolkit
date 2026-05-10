# =====================================================
# 🖥️ ProjectPaths HMI 
# =====================================================
import os
import json
import time
from .root_finder import GetRoot  

class ProjectPaths:
    def __init__(self, root_dir=None, tag="HMI", create_structure=True):
        self.TAG = tag
        print(f"⚙️ [{self.TAG}] Inicializando ProjectPaths...")
        # ROOT único (si no lo mandan, aquí se decide)
        if not root_dir:
            root_dir = GetRoot(verbose=True)
        self.ROOT_DIR = os.path.abspath(root_dir)
        print(f"📁 [{self.TAG} Paths] ROOT_DIR = {self.ROOT_DIR}")
        self.DATA_DIR = os.path.join(self.ROOT_DIR, "Data")
        if not os.path.isdir(self.DATA_DIR):
            raise RuntimeError(f"[FATAL PATHS] ROOT inválido, falta Data: {self.DATA_DIR}")
        # === Carpetas ===
        self.CFG_DIR       = os.path.join(self.DATA_DIR, "CFG")
        self.MARKET_DIR    = os.path.join(self.DATA_DIR, "Market Data")
        self.PROCESS_DIR   = os.path.join(self.DATA_DIR, "Process Data")
        self.SUMMARY_DIR   = os.path.join(self.DATA_DIR, "Summary Data")
        self.ORDERBOOK_DIR = os.path.join(self.DATA_DIR, "OrderBook Data")
        self.ML_DIR        = os.path.join(self.DATA_DIR, "ML")
        self.CHATBOT_DIR   = os.path.join(self.DATA_DIR, "ChatBot_Context")
        self.CFG_FILE1     = os.path.join(self.CFG_DIR, "cfg_1.json")
        self.CFG_FILE2     = os.path.join(self.CFG_DIR, "cfg_2.json")
        self.CFG_FILE3     = os.path.join(self.CFG_DIR, "cfg_3.json")

        if create_structure:
            self._ensure_dirs()
            self._ensure_cfg()
        print(f"🟢 [{self.TAG}] Directorios y configuraciones listas.\n")
        # =====================================================
        # 🧹 Clean scheduler (homologado)
        # =====================================================
        self.cooldown   = 600  # segundos (10 min)
        state = self.manage_json(self.CFG_FILE3 , "read", default={})
        if self.TAG not in state:
            state[self.TAG] = 0
            self.manage_json(self.CFG_FILE3 , "write", state)
    # -------------------------------------------------------------------------------------------------
    def _ensure_dirs(self):
        print("🗂️ [HMI] Verificando estructura de carpetas...")
        dirs = [self.DATA_DIR,
                self.CFG_DIR,
                self.MARKET_DIR,
                self.PROCESS_DIR,
                self.ML_DIR,
                self.SUMMARY_DIR,
                self.ORDERBOOK_DIR,
                self.CHATBOT_DIR]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            print(f"📁   → OK: {d}")
    # -------------------------------------------------------------------------------------
    def should_clean(self):
        state = self.manage_json(self.state_file, "read", default={})
        last  = state.get(self.TAG, 0)
        now   = time.time()
        if last == 0 or (now - last) >= self.cooldown:
            self._update_clean_time(state, now)
            return True
        return False
    def _update_clean_time(self, state=None, now=None):
        if state is None:
            state = self.manage_json(self.state_file, "read", default={})
        if now is None:
            now = time.time()
        state[self.TAG] = now
        self.manage_json(self.state_file, "write", state)
    # -------------------------------------------------------------------------------------------------
    def _ensure_cfg(self):
        print("⚙️ [HMI] Verificando archivos CFG...")
        if not os.path.exists(self.CFG_FILE1):
            self.manage_json(self.CFG_FILE1,"write",{"asset": "BTC"})
            print(f"🆕 [CFG] Creado cfg_1.json → {self.CFG_FILE1}")
        else:
            print(f"📖 [CFG] cfg_1.json cargado.")
        if not os.path.exists(self.CFG_FILE2):
            default2 = {"train_interval": 1800,
                        "pause_between_intervals": 5,
                        "pause_between_cycles": 10,
                        "selected_models": []}
            self.manage_json(self.CFG_FILE2,"write",default2)
            print(f"🆕 [CFG] Creado cfg_2.json → {self.CFG_FILE2}")
        else:
            print(f"📖 [CFG] cfg_2.json cargado.")
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
    def market_file(self, tf):      return os.path.join(self.MARKET_DIR, f"Market_Data_{tf}s.json")
    def process_file(self, tf):     return os.path.join(self.PROCESS_DIR, f"Process_Data_{tf}s.json")
    def summary_file(self, tf):     return os.path.join(self.SUMMARY_DIR, f"Summary_Data_{tf}s.json")
    def orderbook_met_file(self):   return os.path.join(self.ORDERBOOK_DIR, "OrderBook_Metrics.json")
    def orderbook_flat_file(self):  return os.path.join(self.ORDERBOOK_DIR, "OrderBook_Flat.json")
    def orderbook_state_file(self): return os.path.join(self.ORDERBOOK_DIR, "OrderBook_States.json")
