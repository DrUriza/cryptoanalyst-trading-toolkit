# =====================================================
# 🧭 ProjectPaths TA
# =====================================================
import os
import json
import time
from .root_finder import GetRoot

class ProjectPaths:
    def __init__(self, root_dir=None, tag="TA", create_structure=True):
        self.TAG = tag
        print(f"⚙️ [{self.TAG}] Inicializando ProjectPaths...")

        # ROOT único
        if not root_dir:
            root_dir = GetRoot(verbose=True)
        self.ROOT_DIR = os.path.abspath(root_dir)
        print(f"📁 [{self.TAG} Paths] ROOT_DIR = {self.ROOT_DIR}")

        # Rutas base
        self.DATA_DIR = os.path.join(self.ROOT_DIR, "Data")

        # ✅ Si se permite, crea estructura ANTES del check fatal
        if create_structure:
            os.makedirs(self.DATA_DIR, exist_ok=True)

        if not os.path.isdir(self.DATA_DIR):
            raise RuntimeError(f"[FATAL PATHS] ROOT inválido, falta Data: {self.DATA_DIR}")

        # === Carpetas ===
        self.CFG_DIR        = os.path.join(self.DATA_DIR, "CFG")
        self.MARKET_DIR     = os.path.join(self.DATA_DIR, "Market Data")
        self.ORDERBOOK_DIR  = os.path.join(self.DATA_DIR, "OrderBook Data")
        self.PROCESS_DIR    = os.path.join(self.DATA_DIR, "Process Data")
        self.SUMMARY_DIR    = os.path.join(self.DATA_DIR, "Summary Data")
        self.MASTER_DIR     = os.path.join(self.DATA_DIR, "Master Data")
        self.REDVAL_DIR     = os.path.join(self.DATA_DIR, "RedVal Results")
        self.REDVAL_FILES   = os.path.join(self.REDVAL_DIR, "Files")
        self.REDVAL_REPORTS = os.path.join(self.REDVAL_DIR, "Reports")

        # CFG files
        self.CFG_FILE1 = os.path.join(self.CFG_DIR, "cfg_1.json")  # owner: HMI
        self.CFG_FILE3 = os.path.join(self.CFG_DIR, "cfg_3.json")  # shared state

        if create_structure:
            self._ensure_dirs()
            self._ensure_cfg()

        print(f"🟢 [{self.TAG}] Directorios y configuraciones listas.\n")

        # =====================================================
        # 🧹 Clean scheduler (homologado)
        # =====================================================
        self.cooldown = 600  # 10 min
        state = self.manage_json(self.CFG_FILE3, "read", default={}, create_if_missing=True)

        if not isinstance(state, dict):
            state = {}

        if self.TAG not in state:
            state[self.TAG] = 0
            self.manage_json(self.CFG_FILE3, "write", data=state, create_if_missing=True)

    # -------------------------------------------------
    def _ensure_cfg(self):
        print(f"⚙️ [{self.TAG}] Verificando archivos CFG...")

        # ✅ cfg_1 NO se crea aquí (HMI lo crea). Solo avisar.
        if os.path.exists(self.CFG_FILE1):
            print("📖 [CFG] cfg_1.json detectado (solo lectura).")
        else:
            print("⚠️ [CFG] cfg_1.json NO existe (TA usará defaults en memoria).")

        # ✅ cfg_3 sí puede crearse (shared)
        if not os.path.exists(self.CFG_FILE3):
            self.manage_json(self.CFG_FILE3, "write", data={"last_clean": 0}, create_if_missing=True)
            print(f"🆕 [CFG] Creado cfg_3.json → {self.CFG_FILE3}")
        else:
            print("📖 [CFG] cfg_3.json cargado.")

    # -------------------------------------------------
    def _ensure_dirs(self):
        print(f"🗂️ [{self.TAG}] Verificando estructura de carpetas...")
        dirs = [
            self.DATA_DIR,
            self.CFG_DIR,
            self.MARKET_DIR,
            self.ORDERBOOK_DIR,
            self.SUMMARY_DIR,
            self.PROCESS_DIR,
            self.MASTER_DIR,
            self.REDVAL_DIR,
            self.REDVAL_FILES,
            self.REDVAL_REPORTS,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            print(f"📁   → OK: {d}")

    # -------------------------------------------------
    def manage_json(self, filepath, mode="read", data=None, default=None, create_if_missing=False):
        if mode == "read":
            if not os.path.exists(filepath):
                print(f"⚠️ [JSON] No existe → {filepath} utilizando default → {default}")
                if create_if_missing:
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    tmp = filepath + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(default if default is not None else {}, f, indent=4)
                    os.replace(tmp, filepath)
                    print(f"🆕 [JSON] Creado default → {filepath}")
                    return default if default is not None else {}
                return default
            try:
                print(f"📖 [JSON] Read → {filepath}")
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                print(f"⚠️ [WARN] JSON corrupto → {filepath}")
                if create_if_missing:
                    try:
                        tmp = filepath + ".tmp"
                        with open(tmp, "w", encoding="utf-8") as f:
                            json.dump(default if default is not None else {}, f, indent=4)
                        os.replace(tmp, filepath)
                        print(f"🧹 [JSON] Reparado con default → {filepath}")
                        return default if default is not None else {}
                    except Exception:
                        pass
                return default
        elif mode == "write":
            if not create_if_missing and not os.path.exists(os.path.dirname(filepath)):
                raise RuntimeError(f"[FATAL JSON] No existe el directorio destino: {os.path.dirname(filepath)}")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            try:
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        current = json.load(f)
                    if current == data:
                        print(f"⏭️ [JSON] Sin cambios → {filepath}")
                        return False
            except Exception:
                pass
            tmp = filepath + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(tmp, filepath)
            print(f"💾 [JSON] Saved → {filepath}")
            return True
        else:
            raise ValueError("mode must be 'read' or 'write'")
    # -------------------------------------------------------------------------------------
    # 🧹 Clean scheduler (homologado)
    # -------------------------------------------------------------------------------------
    def should_clean(self):
        state = self.manage_json(self.CFG_FILE3, "read", default={}, create_if_missing=True)
        if not isinstance(state, dict):
            state = {}

        last = state.get(self.TAG, 0)
        now  = time.time()

        if last == 0 or (now - last) >= self.cooldown:
            self._update_clean_time(state, now)
            return True

        return False

    def _update_clean_time(self, state=None, now=None):
        if state is None:
            state = self.manage_json(self.CFG_FILE3, "read", default={}, create_if_missing=True)
            if not isinstance(state, dict):
                state = {}

        if now is None:
            now = time.time()

        state[self.TAG] = now
        self.manage_json(self.CFG_FILE3, "write", data=state, create_if_missing=True)

    # =====================================================
    # Helpers cfg_1 (solo lectura)
    # =====================================================
    def read_cfg1_asset(self, default_asset="BTCUSD"):
        cfg1 = self.manage_json(self.CFG_FILE1, "read", default=None, create_if_missing=False)
        if isinstance(cfg1, dict) and cfg1.get("asset"):
            return str(cfg1["asset"])
        return default_asset

    # =====================================================
    # Rutas públicas
    # =====================================================
    def market_file(self, tf):        return os.path.join(self.MARKET_DIR,    f"Market_Data_{tf}s.json")
    def process_file(self, tf):       return os.path.join(self.PROCESS_DIR,   f"Process_Data_{tf}s.json")
    def summary_file(self, tf):       return os.path.join(self.SUMMARY_DIR,   f"Summary_Data_{tf}s.json")
    def master_file(self, tf):        return os.path.join(self.MASTER_DIR,    f"Master_Data_{tf}s.json")
    def redval_file(self, tf):        return os.path.join(self.REDVAL_FILES,  f"RedVal_{tf}s.json")
    def orderbook_flat_file(self):    return os.path.join(self.ORDERBOOK_DIR, "OrderBook_Flat.json")
    def orderbook_metric_file(self):  return os.path.join(self.ORDERBOOK_DIR, "OrderBook_Metrics.json")
    def orderbook_states_file(self):  return os.path.join(self.ORDERBOOK_DIR, "OrderBook_States.json")
