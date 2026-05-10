# =====================================================
# EngineTA - Universal (PY + EXE)
# =====================================================
import os
import sys
import time
import traceback
import argparse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(CURRENT_DIR, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Importaciones reales del core
from TechAnalyze.Cores.root_finder import GetRoot
from TechAnalyze.mainTechAnalyze   import TechAnalyzeApp

def parse_args():
    parser = argparse.ArgumentParser(description="EngineTA - Lanzador universal")
    parser.add_argument("--root", type=str, help="Ruta del proyecto")
    parser.add_argument("--tf", dest="intervals", action="append", type=int)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()

def resolve_root(cli_root):
    if cli_root:
        root = os.path.abspath(cli_root)
        print("[EngineTA] ROOT desde CLI ->", root)
        return root
    root = os.path.abspath(GetRoot(verbose=True))
    print("[EngineTA] ROOT auto ->", root)
    return root

def main():
    args = parse_args()
    ROOT = resolve_root(args.root)
    print(">>> EngineTA INICIADO")
    print("[TA] ROOT =", ROOT)
    print("[TA] SRC  =", SRC)
    # Inicializa TechAnalyzeApp (paths + limpieza incluida)
    app = TechAnalyzeApp(root_dir=ROOT, debug=args.debug)
    intervals = args.intervals or [60, 120, 300, 900]
    print("\n=======================================")
    print(">>> TechAnalyze corriendo continuamente...")
    print("Intervals =", intervals)
    print("=======================================\n")
    while True:
        try:
            app.run_all(intervals)
            time.sleep(1)
        except Exception as e:
            print("\n[ERROR][TechAnalyze LOOP]")
            print(e)
            print(traceback.format_exc())
            time.sleep(1)
if __name__ == "__main__":
    main()
