# =====================================================
# EngineML - Universal (solo .py, pero portable)
# =====================================================

import os
import sys
import argparse

# =====================================================
# 0) PREPARAR sys.path ANTES DE CUALQUIER IMPORT
# =====================================================
CURRENT = os.path.dirname(os.path.abspath(__file__))     # .../MLFramework
SRC     = os.path.join(CURRENT, "src")                   # .../MLFramework/src
PKG     = os.path.join(SRC, "MLFramework")               # .../MLFramework/src/MLFramework

# Insertar rutas si no están
for p in (SRC, PKG):
    if p not in sys.path:
        sys.path.insert(0, p)

print("[EngineML] sys.path configurado:")
print("    SRC =", SRC)
print("    PKG =", PKG)

# =====================================================
# 1) IMPORTS (ya con sys.path correcto)
# =====================================================
from MLFramework.Cores.root_finder   import GetRoot
from MLFramework.mainMLFramework     import MLFrameworkApp
# =====================================================
# 2) Función para resolver ROOT
# =====================================================
def resolve_root(cli_root):
    if cli_root:
        root = os.path.abspath(cli_root)

        # Autocorrección si el usuario pasa /Data
        if os.path.basename(root).lower() == "data":
            print("\n[WARNING][EngineML] Pasaste /Data como root, ajustando al directorio padre.\n")
            root = os.path.dirname(root)

        print(f"[EngineML] ROOT → {root}")
        return root

    # fallback
    root = GetRoot()
    print("[EngineML] ROOT desde GetRoot() →", root)
    return root


# =====================================================
# 3) CLI
# =====================================================
def parse_args():
    parser = argparse.ArgumentParser(description="EngineML Universal")
    parser.add_argument("--root", type=str, help="Ruta raíz del proyecto (carpeta padre de Data).")
    parser.add_argument("--tf", dest="intervals", action="append", type=int, help="Timeframes")
    parser.add_argument("--models", nargs="*", help="Modelos")
    return parser.parse_args()


# =====================================================
# 4) MAIN
# =====================================================
def main():
    args = parse_args()
    ROOT = resolve_root(args.root)

    # VALIDAR EXISTENCIA DE /Data
    DATA_DIR = os.path.join(ROOT, "Data")
    if not os.path.exists(DATA_DIR):
        print("\n❌ [ENGINE ML] La carpeta /Data NO existe en:")
        print("   →", DATA_DIR)
        print("   Ejecuta primero EngineTA para generar Market/Process/RedVal.\n")
        return

    # Inicializar paths y framework
    app = MLFrameworkApp(ROOT)


    intervals = args.intervals or [60, 120, 300, 900]
    models    = args.models or None

    print("\n[START] MLFramework")
    print("ROOT     :", ROOT)
    print("Intervals:", intervals)
    print("Models   :", models)
    print()

    app.run(intervals, models=models)

    print("\n[END] MLFramework\n")


if __name__ == "__main__":
    main()
