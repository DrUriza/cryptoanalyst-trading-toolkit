# =====================================================
# Interface Package
# Contiene los módulos de interfaz y callbacks:
# - RenderManager: maneja los callbacks Dash
# - RenderServer: instancia el servidor y registra callbacks
# =====================================================

from .render_manager import RenderManager
from .render_server  import RenderServer, BrowserController

__all__ = ["RenderManager", 
           "RenderServer", "BrowserController"]
