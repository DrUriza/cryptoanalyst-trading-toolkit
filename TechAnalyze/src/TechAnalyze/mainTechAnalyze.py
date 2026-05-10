# =====================================================
# mainTechAnalyze.py
# TechAnalyze Framework - Coordinador de Pipeline Técnico
# =====================================================
# Autor:       Ottmar Uriza
# Versión:     2.0.0
# Descripción: Ejecuta los módulos principales de TechAnalyze:
#              API → Analyze → Master Data → Reduction
# =====================================================
import os
import shutil
import warnings
import json
import pandas               as pd
from .DataExtract           import DataExtractPipeline
from .Tech.ta_pipeline      import TechAnalyzePipeline
from .Reduction             import ReductionPipeline
from .Cores                 import ProjectPaths

warnings.simplefilter("ignore")

class TechAnalyzeApp:
    def __init__(self, root_dir, debug=True):
        self.root_dir  = os.path.abspath(root_dir)
        self.paths     = ProjectPaths(self.root_dir) 
        self.debug     = debug
        self.loop_coun = {}
        self.trigger_n = 5   # cada 5 ciclos corre TA con PCA/Reduction
        print(f"🟢 TechAnalyzeApp inicializado en: {self.root_dir}")
        # 🔥 Ya no CleanManager — limpieza integrada en ProjectPaths
        if self.paths.should_clean():
            print("🧹 [TechAnalyze] Limpieza inicial...")
            self._clean_env()   # tu función de limpieza queda igual
    # =====================================================
    # Limpieza avanzada de entorno (Trash)
    # =====================================================
    def _clean_env(self):
        base_dir  = os.path.abspath(self.root_dir)
        trash_dir = os.path.join(base_dir, "Trash")
        os.makedirs(trash_dir, exist_ok=True)
        print("🧹 [TechAnalyze] Limpieza optimizada iniciada...")
        EXT_BASURA = (".log", ".tmp", ".cache", ".bak")
        CARPETAS_PROHIBIDAS = {os.path.join(base_dir, "Data"),trash_dir}
        for root, dirs, files in os.walk(base_dir):
            # Evitar entrar a /Data
            if any(root.startswith(bad) for bad in CARPETAS_PROHIBIDAS):
                continue
            # Limpiar __pycache__
            for d in list(dirs):
                if d == "__pycache__":
                    path = os.path.join(root, d)
                    try:
                        shutil.rmtree(path)
                        print(f"[CLEAN] Eliminado pycache → {path}")
                    except Exception:
                        pass
                    dirs.remove(d)
            # Eliminar archivos basura
            for f in files:
                if f.endswith(EXT_BASURA):
                    try:
                        os.remove(os.path.join(root, f))
                    except:
                        pass
        print("🧹 [TechAnalyze] Limpieza completada.\n")
    # =====================================================
    # Crear los IDs de IB
    # =====================================================  
    @staticmethod
    def build_tfids(intervals):
        base = 100
        return {tf: base + (i + 1) for i, tf in enumerate(intervals)}
    # =====================================================
    # 1) Market API
    # =====================================================
    def run_api(self, tf, intervals, fetch_only=False, bootstrap=False):
        try:
            tfids = self.build_tfids(intervals)
            print("🟡 [API] Extrayendo Market Data + OrderBook...")
            pipe = DataExtractPipeline(self.paths, tf, tfids)
            pipe.run(capture_orderbook=(tf == 60 or tf == 300),bootstrap=bootstrap)
            print("🟢 [API] DataExtract completado")
            pipe._ib_disconnect()
            if fetch_only:
                return
        except Exception as e:
            print(f"❌ [ERROR][API] {e}")
            if bootstrap:
                raise
    # =====================================================
    # 2) Technical Analysis
    # =====================================================
    def run_tech_analyze(self, interval,cycle=0):
        try:
            print(f"🧠 [TA] Ejecutando análisis técnico TF={interval}s")
            pipeline = TechAnalyzePipeline(self.paths)
            if cycle == 0:
                pipeline.run_analysis(interval)
            else:
                pipeline.run_analysis(interval,cycle)  
            print(f"🟢 [TA] Análisis técnico completado TF={interval}s")
        except Exception as e:
            print(f"❌ [ERROR][TechAnalyze][{interval}s]: {e}")
    # =====================================================
    # 3) Master + Reduction
    # =====================================================
    def run_master_pipeline(self, interval):
        try:
            reduction = ReductionPipeline(paths=self.paths, interval=interval)
            reduction.run()
            print(f"💾 [TechAnalyze] Master + Reduction completado @ {interval}s")
        except Exception as e:
            print(f"[ERROR][MasterPipeline][{interval}s]: {e}")
    # =====================================================
    # 4) Actuliza solo market data
    # =====================================================
    def update_process_with_market(self, tf):
        # Paths fijos
        market_path  = self.paths.market_file(tf)
        process_path = self.paths.process_file(tf)
        # Leer ambos JSON 
        market  = self.paths.manage_json(filepath=market_path,  mode="read", default=[])
        process = self.paths.manage_json(filepath=process_path, mode="read", default=[])
        df_market  = pd.DataFrame(market)
        df_process = pd.DataFrame(process)
        # Campos originales de MarketData
        market_fields = ["open", "high", "low", "close", "volume","spread", "timestamp", "Color", "buy_volume", "sell_volume"]
        # Reemplazar SOLO campos de MarketData
        for col in market_fields:
            if col in df_market.columns and col in df_process.columns:
                df_process[col] = df_market[col]
            else:
                print(f"⚠️ Campo no encontrado en alguna estructura → {col}")
        # Guardar usando ProjectPaths.manage_json
        self.paths.manage_json(filepath=process_path,mode="write",data=json.loads(df_process.to_json(orient="records")),default={})
        print(f"📄 [ProcessUpdate] MarketData integrado en Process_Data_{tf}s.json ")
    # =====================================================
    # 5) Orquestador General
    # =====================================================
    def run_all(self, intervals):
        # Inicializar contadores
        for tf in intervals:
            if tf not in self.loop_coun:
                self.loop_coun[tf] = 0
        # Limpieza periódica
        if self.paths.should_clean():
            print("🧹 [TechAnalyze] Ejecutando limpieza periódica...")
            self._clean_env()
        else:
            print("🧹 [TechAnalyze] Limpieza omitida")
        # Loop por timeframe
        for tf in intervals:
            cycle = self.loop_coun[tf]
            print(f"\n⏱️ [LOOP] TF {tf}s → ciclo #{cycle}")
            # =====================================================
            # 🔵 CICLO 0 → BOOTSTRAP COMPLETO
            # =====================================================
            if cycle == 0:
                print(f"🚀 [BOOTSTRAP] TF={tf}s → Market + TA + Reduction")
                self.run_api(tf, intervals, fetch_only=True, bootstrap=True)
                print(f"\n🔵 ========== Análisis Técnico TF={tf}s ==========")
                self.run_tech_analyze(tf)
                self.run_master_pipeline(tf)
                self.loop_coun[tf] = 1
                continue
            # =====================================================
            # 🔵 CICLOS 1 → trigger_n-1 → SOLO MARKET
            # =====================================================
            if cycle < self.trigger_n:
                self.run_api(tf, intervals, fetch_only=True)
                self.run_tech_analyze(tf,cycle)
                print(f"⏳ [MARKET ONLY] TF={tf}s (ciclo {cycle})")
                self.loop_coun[tf] += 1
                continue
            # =====================================================
            # 🔵 CICLO FINAL (trigger_n) → MARKET + TA + REDUCTION
            # =====================================================
            if cycle == self.trigger_n:
                print(f"🏁 [FINAL CYCLE] TF={tf}s → Market + TA + Reduction")
                self.run_api(tf, intervals, fetch_only=True)
                print(f"\n🔵 ========== Análisis Técnico TF={tf}s ==========")
                self.run_tech_analyze(tf)
                print(f"\n🟣 ========== Master + Reduction TF={tf}s ==========")
                self.run_master_pipeline(tf)
                # 🔁 RESET A CICLO 1 (NO 0)
                self.loop_coun[tf] = 1
                continue
