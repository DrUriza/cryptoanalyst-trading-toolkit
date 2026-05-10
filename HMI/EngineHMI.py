# EngineHMI - Universal (py + exe)

import os
import sys
import time
import traceback
import threading
import argparse

# ---------------------------------------------------------
# Ensure /src is importable
# ---------------------------------------------------------
def ensure_src_on_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    hmi_src = os.path.join(current_dir, "src")
    if hmi_src not in sys.path:
        sys.path.insert(0, hmi_src)
    return hmi_src

HMI_SRC = ensure_src_on_path()
# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="EngineHMI - Lanzador universal de HMIApp (Dash)")
    parser.add_argument("--root", type=str, help="Ruta raíz del proyecto (donde vive /Data)")
    parser.add_argument("--port", type=int, default=8085, help="Puerto HTTP (default 8080)")
    parser.add_argument("--debug", action="store_true", help="Modo debug Dash")
    return parser.parse_args()
# ---------------------------------------------------------
# Start HMI (thread)
# ---------------------------------------------------------
def start_hmi(root, port, debug):
    try:
        hmi_src = ensure_src_on_path()
        from HMI.mainHMI import HMIApp
        print("[HMI] ROOT =", root)
        print("[HMI] SRC  =", hmi_src)
        hmi = HMIApp(root_dir=root, port=port, debug=debug)  # root puede ser None
        hmi.run()
    except Exception as e:
        print("\n[ERROR][HMI THREAD]")
        print(e)
        print(traceback.format_exc())
# ---------------------------------------------------------
# Main (auto-restart)
# ---------------------------------------------------------
def main():
    args = parse_args()
    # Si viene root por CLI, normalízalo a absoluto
    cli_root = os.path.abspath(args.root) if args.root else None
    print("\n=======================================")
    print(">>> EngineHMI corriendo SIEMPRE...")
    print("ROOT (CLI) =", cli_root)
    print("PORT       =", args.port)
    print("DEBUG      =", args.debug)
    print("=======================================\n")
    while True:
        t = threading.Thread(target=start_hmi, kwargs={"root": cli_root, "port": args.port, "debug": args.debug}, daemon=True)
        t.start()
        while t.is_alive():
            time.sleep(1)
        print("[HMI] El servidor murió, reiniciando...\n")
if __name__ == "__main__":
    main()
