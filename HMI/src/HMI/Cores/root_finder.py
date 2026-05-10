# root_finder.py (UNIVERSAL: HMI/TA/ChatBot, modo SOLO y modo TODO)
import os
import sys
import __main__
from pathlib import Path

ENV_ROOT   = "ELATIN_ROOT"
MARKER     = "ELATIN.ROOT"   # archivo vacío en el ROOT
MAX_UP     = 15

HINT_DIRS  = ("Exe", "HMI", "TechAnalyze", "Chatbot")
HINT_FILES = ("EngineApp.exe",)

def _safe_resolve(p: Path) -> Path:
    try:
        return p.expanduser().resolve()
    except Exception:
        return Path(os.path.abspath(str(p)))

def _as_dir(p: Path) -> Path:
    return p.parent if p.is_file() else p

def _is_suspicious(candidate: Path) -> bool:
    s = str(candidate).lower()
    return ("_mei" in s) or ("appdata\\local\\temp" in s) or ("\\temp\\" in s) or ("/tmp/" in s)

def _start_points():
    pts = []
    if getattr(sys, "frozen", False):
        pts.append(Path(sys.executable))
    main_file = getattr(__main__, "__file__", None)
    if main_file:
        pts.append(Path(main_file))
    pts.append(Path(__file__))
    pts.append(Path.cwd())
    if sys.argv and sys.argv[0]:
        pts.append(Path(sys.argv[0]))

    uniq = []
    for p in pts:
        rp = _safe_resolve(p)
        if rp not in uniq:
            uniq.append(rp)
    return uniq

def _score(candidate: Path) -> int:
    s = 0
    if _is_suspicious(candidate):
        s -= 10_000  # jamás elegir temp si hay otra opción

    if (candidate / MARKER).is_file(): s += 1000
    if (candidate / "Data").is_dir():  s += 200

    for d in HINT_DIRS:
        if (candidate / d).is_dir():
            s += 40

    for f in HINT_FILES:
        if (candidate / f).is_file():
            s += 60

    # bonus si ya tiene subcarpetas típicas dentro de Data
    typical = ("CFG", "Market Data", "Process Data", "Summary Data", "OrderBook Data")
    data = candidate / "Data"
    if data.is_dir():
        for td in typical:
            if (data / td).is_dir():
                s += 10

    return s

def _ensure_data(root: Path, verbose: bool):
    data_dir = root / "Data"
    if not data_dir.is_dir():
        data_dir.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"[ROOT] Data creada -> {data_dir}")

def GetRoot(verbose=True, create_data=True) -> str:
    """
    Orden:
    1) --root <path>  (si falta Data y create_data=True, la crea)
    2) ENV ELATIN_ROOT (igual)
    3) Auto: subir y escoger mejor score (marker>data+hints), y crear Data si falta
    """

    # 1) CLI
    if "--root" in sys.argv:
        i = sys.argv.index("--root")
        if i + 1 < len(sys.argv):
            forced = _safe_resolve(Path(sys.argv[i + 1]))
            if _is_suspicious(forced):
                raise RuntimeError(f"[FATAL ROOT] --root apunta a ruta temporal/sospechosa: {forced}")
            if create_data:
                _ensure_data(forced, verbose)
            if verbose:
                print(f"[ROOT] --root => {forced}")
            return str(forced)

    # 2) ENV
    env = os.environ.get(ENV_ROOT)
    if env:
        forced = _safe_resolve(Path(env))
        if _is_suspicious(forced):
            raise RuntimeError(f"[FATAL ROOT] ENV {ENV_ROOT} apunta a ruta temporal/sospechosa: {forced}")
        if create_data:
            _ensure_data(forced, verbose)
        if verbose:
            print(f"[ROOT] ENV {ENV_ROOT} => {forced}")
        return str(forced)

    # 3) AUTO
    best = None
    best_score = -10_000_000
    best_from = None

    checked = []
    for start in _start_points():
        cur = _as_dir(start)
        for _ in range(MAX_UP):
            checked.append(str(cur))
            sc = _score(cur)
            if sc > best_score:
                best_score = sc
                best = cur
                best_from = start

            if cur.parent == cur:
                break
            cur = cur.parent

    if not best or _is_suspicious(best):
        raise RuntimeError(
            "[FATAL ROOT] No encontré un ROOT válido (solo rutas temporales tipo _MEI/Temp).\n"
            "Solución: pasa --root o define ELATIN_ROOT con la carpeta del proyecto."
        )

    if create_data:
        _ensure_data(best, verbose)

    if verbose:
        print(f"[ROOT] auto from: {best_from}")
        print(f"[ROOT] ROOT = {best} (score={best_score})")
        print(f"[ROOT] Data = {best/'Data'}")

    return str(best)
