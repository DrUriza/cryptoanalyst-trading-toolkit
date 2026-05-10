# =====================================================
# mainHMI.py – Versión Homologada 2.2.0
# =====================================================
import os
import shutil
from dash                           import Dash, dcc, html
from .Cores.project_path            import ProjectPaths
from .Cores.cleaner_manager         import CleanManager
from .Cores.traces_manager          import TraceManager

from .Components.plots_manager      import PlotManager
from .Components.ml_manager         import MLManager
from .Components.orderbook_manager  import OrderBookManager
from .Components.techresume_manager import TechResumeManager
from .Components.chatbot_manager    import ChatBotManager  

from .Interface.render_manager      import RenderManager
from .Interface.render_server       import RenderServer, BrowserController

class HMIApp:
    def __init__(self, root_dir=None, port=8054, debug=True):
        self.paths    = ProjectPaths(root_dir, tag="HMI")
        self.root_dir = self.paths.ROOT_DIR
        print("🟢 HMIApp inicializado en:", self.root_dir)
        self.port  = port
        self.debug = debug
        # Cleaner
        self.cleaner = CleanManager(self.paths, cooldown_minutes=20)
        if self.cleaner.should_clean():
            self._clean_env()
        # Dash
        self.app = Dash(__name__, suppress_callback_exceptions=True)
        self.app.title = "Elatin Trading App"
        asset = self._build_layout()
        self._init_managers(asset)


    # =====================================================
    # CLEANER
    # =====================================================
    def _clean_env(self):
        for base, dirs, _ in os.walk(self.root_dir):
            if "__pycache__" in dirs:
                shutil.rmtree(os.path.join(base, "__pycache__"), ignore_errors=True)
        print("🧹 [HMI] Limpieza completada")

    # =====================================================
    # LAYOUT
    # =====================================================
    def _build_layout(self):
        initial_asset = "BTC"

        self.app.layout = html.Div([
            html.H1("📊 Elatin Trading App", style={"textAlign": "center"}),
            dcc.Interval(id="datetime-interval", interval=1000, n_intervals=0),
            html.Div(id="datetime-display", style={"textAlign": "center", "marginTop": "10px"}),

            dcc.Dropdown(id="asset-dropdown", 
                         options=[{"label": "BTC", "value": "BTC"},{"label": "AMAZON", "value": "AMZN"},
                                  {"label": "SILVER", "value": "SLV"},{"label": "TESLA", "value": "TSLA"},
                                  {"label": "NASDAQ", "value": "QQQ"}],
                         value=initial_asset,
                         style={"width": "250px", "margin": "auto"}),
            dcc.Store(id="cfg1-sync", data={}),
            dcc.Tabs(id="tabs", value="intermediate", children=[dcc.Tab(label="📈 Intermediate", value="intermediate"),
                                                                dcc.Tab(label="⚡ Fast", value="fast"),
                                                                dcc.Tab(label="📊 OrderBook", value="orderbook"),
                                                                dcc.Tab(label="📝 Report", value="report")]),
            html.Div(id="tabs-content"),
            # ================================
            # 🤖 CHATBOT UI
            # ================================
            html.Div("💬", 
                     id="chatbot-toggle",
                     style={ "position": "fixed",
                    "bottom": "25px",
                    "right": "25px",
                    "width": "60px",
                    "height": "60px",
                    "backgroundColor": "#9B59B6",
                    "color": "white",
                    "borderRadius": "50%",
                    "textAlign": "center",
                    "lineHeight": "60px",
                    "fontSize": "32px",
                    "cursor": "pointer",
                    "zIndex": "9999"}),
            html.Div([html.H4("🤖 Elatin Chat Assistant", style={"textAlign": "center"}),
                dcc.Input(id="chatbot-input",
                          type="text",
                          placeholder="Escribe tu pregunta...",
                          style={"width": "100%", "marginBottom": "10px"}),
                html.Button("Enviar", id="btn-chatbot-send", style={"backgroundColor": "#9B59B6", "color": "white"}),
                html.Div(id="chatbot-output", style={"marginTop": "15px"})],
                id="chatbot-window",
                style={"position": "fixed",
                       "bottom": "100px",
                       "right": "25px",
                       "width": "320px",
                       "backgroundColor": "white",
                       "border": "2px solid #9B59B6",
                       "borderRadius": "12px",
                       "padding": "15px",
                       "display": "none",
                       "zIndex": "9999"})])
        return initial_asset
    # =====================================================
    # MANAGERS
    # =====================================================
    def _init_managers(self, asset):
        cfg = self.paths.manage_json(self.paths.CFG_FILE1, "read") or {}
        cfg["asset"] = asset
        self.paths.manage_json(self.paths.CFG_FILE1, "write", cfg)
        self.traces  = TraceManager(self.paths)
        self.plots   = PlotManager(self.traces)
        self.ml      = MLManager(self.paths.ML_DIR, self.paths)
        self.ob      = OrderBookManager(self.paths.ORDERBOOK_DIR, self.paths)
        self.tr      = TechResumeManager(self.paths.SUMMARY_DIR, self.paths)
        self.chatbot = ChatBotManager(self.app, self.paths)
        self.chatbot.register_callbacks()
        self.render_mgr = RenderManager(self.app, self.plots, self.ml, self.ob, self.tr, self.paths)
        self.render_mgr.register_callbacks()
        self.plot_server = RenderServer(self.plots, port=self.port)
        self.plot_server.register_routes(self.app)
        self.browser = BrowserController(port=self.port)
    
    # =====================================================
    # RUN
    # =====================================================
    def run(self):
        print(f"[HMIApp] 🟢 Servidor en puerto {self.port}")
        self.browser.open_browser()
        self.app.run(port=self.port, debug=self.debug, use_reloader=False)

