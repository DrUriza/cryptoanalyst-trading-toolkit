# =====================================================
# EngineChatbot - Universal (PY + EXE) - LOOP CONTINUO
# =====================================================
import os
import sys
import time
import argparse
import traceback
import json

# -----------------------------------------------------
# 1) Asegurar /src del Chatbot en sys.path (solo imports)
# -----------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))   # .../Libraries/Chatbot
SRC = os.path.join(CURRENT_DIR, "src")                     # .../Libraries/Chatbot/src
if SRC not in sys.path:
    sys.path.insert(0, SRC)
# -----------------------------------------------------
# 2) Imports del Chatbot
# -----------------------------------------------------
from Chatbot.Cores.root_finder import GetRoot
from Chatbot.mainChatBot       import ChatBotApp
# -----------------------------------------------------
# 3) CLI Args
# -----------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="EngineChatbot - Lanzador universal del ChatBotApp")
    parser.add_argument("--root",type=str,help="Ruta raíz del proyecto (donde vive /Data, /Process_Data, etc.)")
    parser.add_argument("--debug",action="store_true",help="Activa modo debug en ChatBotApp")
    return parser.parse_args()
# -----------------------------------------------------
# 4) Resolver ROOT (HOMOLOGADO)
# -----------------------------------------------------
def resolve_root(cli_root: str) -> str:
    if cli_root:
        root = os.path.abspath(cli_root)
    else:
        root = os.path.abspath(GetRoot())
    print("[EngineChatbot] ROOT final ->", root)
    return root
# -----------------------------------------------------
# 5) Utils
# -----------------------------------------------------
def read_created_at(question_file: str):
    if not os.path.exists(question_file):
        return None
    try:
        with open(question_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("created_at")
    except Exception:
        return None
# -----------------------------------------------------
# 6) MAIN LOOP
# -----------------------------------------------------
def main():
    args = parse_args()
    ROOT = resolve_root(args.root)
    print("\n=======================================")
    print("🤖 EngineChatbot INICIADO (LOOP CONTINUO)")
    print("ROOT =", ROOT)
    print("SRC  =", SRC)
    print("DEBUG =", args.debug)
    print("=======================================\n")
    # Inicializar App (ROOT ÚNICO Y DEFINITIVO)
    app = ChatBotApp(root_dir=ROOT, debug=args.debug)
    last_created_at    = None
    processed_ia_files = set()
    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
    print(">>> Esperando cambios en user_question.json o respuestas IA...\n")

    while True:
        try:
            run_zip = False
            run_ia  = False

            # ----------------------------------
            # 1️⃣ Detectar nueva pregunta usuario
            # ----------------------------------
            question_file      = app.paths.chatbot_question_file()
            current_created_at = read_created_at(question_file)
            if current_created_at and current_created_at != last_created_at:
                print("🆕 Nueva pregunta detectada")
                last_created_at = current_created_at
                run_zip = True
            # ----------------------------------
            # 2️⃣ Detectar archivos IA_Response_*.json
            # ----------------------------------
            if os.path.isdir(DOWNLOAD_DIR):
                for fname in os.listdir(DOWNLOAD_DIR):
                    if (fname.startswith("IA_Response_")
                        and fname.endswith(".json")
                        and fname not in processed_ia_files):
                        print(f"📥 Archivo IA detectado -> {fname}")
                        processed_ia_files.add(fname)
                        run_ia = True
                        break
            # ----------------------------------
            # 3️⃣ Ejecutar pipelines
            # ----------------------------------
            if run_zip:
                app.run_ZipC()
            if run_ia:
                app.run_IAI()
            time.sleep(2)
        except Exception as e:
            print("\n[ERROR][EngineChatbot LOOP]")
            print(e)
            print(traceback.format_exc())
            time.sleep(2)

# -----------------------------------------------------
# 7) Entry Point
# -----------------------------------------------------
if __name__ == "__main__":
    main()
