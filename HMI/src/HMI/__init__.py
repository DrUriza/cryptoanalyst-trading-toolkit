# =====================================================
# HMI Framework - Human Machine Interface for Trading Analytics
# =====================================================
# Autor:       Ottmar Uriza
# Versión:     2.0.0
# =====================================================
from .Cores.project_path            import ProjectPaths
from .Cores.traces_manager          import TraceManager
from .Components.plots_manager      import PlotManager
from .Components.ml_manager         import MLManager
from .Components.orderbook_manager  import OrderBookManager
from .Components.techresume_manager import TechResumeManager
from .Interface.render_manager      import RenderManager
from .Interface.render_server       import RenderServer, BrowserController
from .mainHMI                       import HMIApp


__all__ = ["ProjectPaths", "TraceManager", 
           "PlotManager", "MLManager","OrderBookManager", "TechResumeManager",
           "RenderManager","RenderServer","BrowserController",
           "HMIApp"]

__version__ = "2.0.0"

print(f"[HMI v{__version__}] se instaló correctamente y está listo para usarse.")