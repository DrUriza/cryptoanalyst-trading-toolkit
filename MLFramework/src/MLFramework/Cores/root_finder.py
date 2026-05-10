# =====================================================
# root_finder.py – versión universal
# =====================================================
import os
import sys

def GetRoot():
    """
    Devuelve el ROOT real del proyecto, sin importar si se ejecuta desde:
    - EngineML.py
    - EngineTA.py
    - EngineHMI.py
    - EngineHMI.exe
    - Cualquier script dentro de Libraries/
    """

    # Dir donde está el archivo actual (py o exe)
    base = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------
    # 1) Caso: Ejecutable (.exe)
    # ---------------------------------------------
    if getattr(sys, 'frozen', False):
        # EngineHMI.exe → sube 4 niveles
        root = os.path.abspath(os.path.join(base, "..", "..", "..", ".."))
        return root

    # ---------------------------------------------
    # 2) Caso: Scripts .py dentro de Libraries/
    # ---------------------------------------------
    # Subimos hasta encontrar la carpeta raíz (la que contiene Market/Process/RedVal o MLFramework/src)
    current = base
    while True:
        items = set(os.listdir(current))

        # ROOT del TradingElatinApp → contiene estas carpetas
        if {"Market", "Process", "RedVal"}.issubset(items):
            return current

        # ROOT de MLFramework → contiene src/MLFramework
        if "src" in items and "MLFramework" in os.listdir(os.path.join(current, "src")):
            return current

        # Si llegamos al disco, detener
        parent = os.path.dirname(current)
        if parent == current:
            break

        current = parent

    # Si no se detectó correctamente
    raise RuntimeError("No se pudo determinar correctamente el ROOT del proyecto.")
