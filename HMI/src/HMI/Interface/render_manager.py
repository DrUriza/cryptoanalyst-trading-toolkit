# =====================================================
# Interface/render_manager.py
# Render estable con 9 RadioItems (sin overlays)
# =====================================================
from dash            import html, dcc, Output, Input, State, no_update, callback_context
from dash.exceptions import PreventUpdate
import datetime      as dt
import time

class RenderManager:
    def __init__(self, app, plot_mgr, ml_mgr, ob_mgr, tr_mgr, paths):
        self.app = app
        self.plot_mgr = plot_mgr
        self.ml_mgr = ml_mgr
        self.ob_mgr = ob_mgr
        self.tr_mgr = tr_mgr
        self.paths = paths
        self.CFG_DIR = paths.CFG_DIR

    # ==================================================
    # CALLBACKS
    # ==================================================
    def register_callbacks(self):
        # ---------------------------
        # CFG1 SYNC (asset -> CFG_FILE1)
        # ---------------------------
        @self.app.callback(Output("cfg1-sync", "data"),
                           Input("asset-dropdown", "value"),
                           prevent_initial_call=True)
        def sync_cfg1(asset):
            if not asset:
                raise PreventUpdate
            cfg = self.paths.manage_json(self.paths.CFG_FILE1, "read") or {}
            cfg["asset"] = asset
            self.paths.manage_json(self.paths.CFG_FILE1, "write", cfg)
            return {"asset": asset, "ts": time.time()}
        # ---------------------------
        # CLOCK (si existe en layout)
        # ---------------------------
        @self.app.callback(Output('datetime-display', 'children'),
                           Input('datetime-interval', 'n_intervals'),
                           prevent_initial_call=True)
        def update_datetime(_):
            return f"🕒 {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        # ---------------------------
        # TABS
        # ---------------------------
        @self.app.callback(Output("tabs-content", "children"),
                           Input("tabs", "value"))
        def render_tab(tab):
            # =========================
            # INTERMEDIATE
            # =========================
            if tab == "intermediate":
                return html.Div([

                    html.Label("⏱ Select Data Source"),
                    dcc.RadioItems(
                        id="data-source-intermediate",
                        options=[
                            {"label": "15 Min", "value": 900},
                            {"label": "5 Min",  "value": 300}
                        ],
                        value=900,
                        inline=True
                    ),

                    dcc.Dropdown(
                        id="zoom-dropdown-intermediate",
                        options=[
                            {"label": "Zoom x1", "value": 1},
                            {"label": "Zoom x2", "value": 4},
                            {"label": "Zoom x3", "value": 7},
                        ],
                        value=1,
                        style={"width": "200px", "marginTop": "10px"}),
                    html.Hr(),
                    dcc.Interval(id="intermediate-interval", interval=4000, n_intervals=0),
                    # 🔷 DASHBOARD + 9 MINI GRÁFICAS
                    html.Div(id="Intermediate-plots"),
                    html.Hr(),
                    # 🔘 RADIO ITEMS (ABAJO, COMO QUIERES)
                    html.Div([html.Label("📌 Indicador individual:", 
                                         style={"fontSize": "15px", "marginRight": "10px","display": "block",  "marginBottom": "6px"}),
                        dcc.RadioItems(
                            id="single-indicator-radio",
                            options=[
                                {"label": "RSI",        "value": "RSI"},
                                {"label": "Trending",   "value": "Trending"},
                                {"label": "WD",         "value": "WD"},
                                {"label": "ATR",        "value": "ATR"},
                                {"label": "Kalman F",   "value": "Kalman F"},
                                {"label": "Kalman E",   "value": "Kalman E"},
                                {"label": "TSI",        "value": "TSI"},
                                {"label": "MACD",       "value": "MACD"},
                                {"label": "Stochastic", "value": "Stochastic"},
                                {"label": "H&S",        "value": "H&S"},
                                {"label": "Hide","value": "NONE"},
                            ],
                            value="NONE",
                            inline=True,
                            labelStyle={"marginRight": "70px", "fontSize": "15px"})], 
                        style={"marginBottom": "15px"}),

                    # 🔽 SINGLE PLOT (NO overlay)
                    html.Div(id="single-plot-output", style={"marginTop": "15px"})])

            # =========================
            # FAST  (✅ YA NO PLACEHOLDER)
            # =========================
            elif tab == "fast":
                return html.Div([

                    html.Label("⏱ Select Data Source"),
                    dcc.RadioItems(
                        id="data-source-fast",
                        options=[
                            {"label": "2 Min", "value": 120},
                            {"label": "1 Min", "value": 60}
                        ],
                        value=120,
                        inline=True
                    ),

                    dcc.Dropdown(
                        id="zoom-dropdown-fast",
                        options=[
                            {"label": "Zoom x1", "value": 1},
                            {"label": "Zoom x2", "value": 4},
                            {"label": "Zoom x3", "value": 7},
                        ],
                        value=1,
                        style={"width": "200px", "marginTop": "10px"}
                    ),

                    html.Hr(),

                    dcc.Interval(id="fast-interval", interval=4000, n_intervals=0),
                    # 🔷 DASHBOARD + 9 MINI GRÁFICAS
                    html.Div(id="Fast-plots"),
                    html.Hr(),
                    # 🔘 RADIO ITEMS (ABAJO)  ✅ IDs DIFERENTES
                    html.Div([html.Label("📌 Indicador individual:", 
                                         style={"fontSize": "15px", "marginRight": "10px","display": "block",  "marginBottom": "6px"}),
                        dcc.RadioItems(id="single-indicator-radio-fast",
                            options=[{"label": "RSI",        "value": "RSI"},
                                     {"label": "Trending",   "value": "Trending"},
                                     {"label": "WD",         "value": "WD"},
                                     {"label": "ATR",        "value": "ATR"},
                                     {"label": "Kalman F",   "value": "Kalman F"},
                                     {"label": "TSI",        "value": "TSI"},
                                     {"label": "MACD",       "value": "MACD"},
                                     {"label": "Stochastic", "value": "Stochastic"},
                                     {"label": "H&S",        "value": "H&S"},
                                     {"label": "— ocultar —","value": "NONE"}],
                            value="NONE",
                            inline=True,
                            labelStyle={"marginRight": "70px", "fontSize": "15px"})], style={"marginBottom": "10px"}),

                    html.Div(id="single-plot-output-fast", style={"marginTop": "15px"})])
            # =========================
            # ORDERBOOK
            # =========================
            elif tab == "orderbook":
                return html.Div([dcc.Interval(id="orderbook-interval", interval=10000, n_intervals=0),
                                 html.Div(id="orderbook-plots")])
            # =========================
            # REPORT (placeholder estable)
            # =========================
            elif tab == "report":
                return html.Div([html.Div([html.Button("📊 TechResume", id="btn-techresume", n_clicks=0),
                                           html.Button("🤖 MLResume",   id="btn-mlresume",   n_clicks=0)], 
                                           style={"display": "flex", "justifyContent": "center", "gap": "15px","marginBottom": "20px"}),
                                           html.Div(id="report-output")], style={"padding": "20px"})
        # ---------------------------
        # INTERMEDIATE DASHBOARD
        # ---------------------------
        @self.app.callback(Output("Intermediate-plots", "children"),
                           Input("asset-dropdown", "value"),
                           Input("zoom-dropdown-intermediate", "value"),
                           Input("data-source-intermediate", "value"),
                           Input("intermediate-interval", "n_intervals"))
        def update_intermediate(asset, zoom, source, _):
            return self.plot_mgr.build_dashboard(asset, zoom, source)
        # ---------------------------
        # SINGLE INDICATOR (INTERMEDIATE)
        # ---------------------------
        @self.app.callback(Output("single-plot-output", "children"),
                           Input("single-indicator-radio", "value"),
                           State("asset-dropdown", "value"),
                           State("zoom-dropdown-intermediate", "value"),
                           State("data-source-intermediate", "value"),
                           prevent_initial_call=True)
        def update_single_indicator(ind, asset, zoom, source):
            if ind == "NONE":
                return []  # limpia correctamente
            fig = self.plot_mgr.build_single_plot(ind, asset, zoom, source)
            return dcc.Graph(figure=fig)
        # ---------------------------
        # FAST DASHBOARD ✅ REAL
        # ---------------------------
        @self.app.callback(Output("Fast-plots", "children"),
                           Input("asset-dropdown", "value"),
                           Input("zoom-dropdown-fast", "value"),
                           Input("data-source-fast", "value"),
                           Input("fast-interval", "n_intervals"))
        def update_fast(asset, zoom, source, _):
            return self.plot_mgr.build_dashboard(asset, zoom, source)
        # ---------------------------
        # SINGLE INDICATOR (FAST) ✅ IDs separados
        # ---------------------------
        @self.app.callback(Output("single-plot-output-fast", "children"),
                           Input("single-indicator-radio-fast", "value"),
                           State("asset-dropdown", "value"),
                           State("zoom-dropdown-fast", "value"),
                           State("data-source-fast", "value"),
                           prevent_initial_call=True)
        def update_single_indicator_fast(ind, asset, zoom, source):
            if ind == "NONE":
                return []
            fig = self.plot_mgr.build_single_plot(ind, asset, zoom, source)
            return dcc.Graph(figure=fig)
        # ---------------------------
        # ORDERBOOK
        # ---------------------------
        @self.app.callback(Output("orderbook-plots", "children"),
                           Input("orderbook-interval", "n_intervals"),
                           State("asset-dropdown", "value"))
        def update_orderbook(_, asset):
            return self.ob_mgr.render(asset)
        # ---------------------------
        # REPORT TAB (placeholder)
        # ---------------------------
        @self.app.callback(Output("report-output", "children"),
                           Input("btn-techresume", "n_clicks"),
                           Input("btn-mlresume", "n_clicks"),
                           Input("tabs", "value"), 
                           State("asset-dropdown", "value"),
                           prevent_initial_call=True)
        def update_report_buttons(n_tech, n_ml, tab, asset):
            ctx = callback_context
            if not ctx.triggered:
                return no_update
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            # Timeframes que tú ya usas
            timeframes = [60, 120, 300, 900]
            if button_id == "btn-techresume":
                return html.Div([
                    html.H4("📊 Technical Resume"),
                    html.Div([self.tr_mgr.generate_signal_table(tf) for tf in timeframes], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center","gap": "20px"})])
            if button_id == "btn-mlresume":
                return html.Div([
                    html.H4("🤖 ML Resume"),
                    html.Div([self.ml_mgr.generate_ml_table(tf) for tf in timeframes], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center","gap": "20px"})])
            return no_update
        # ---------------------------
        # CHATBOT (BLINDADO)
        # ---------------------------
        @self.app.callback(Output("chatbot-window", "style"),
                           Input("chatbot-toggle", "n_clicks"),
                           State("chatbot-window", "style"),
                           prevent_initial_call=True)
        def toggle_chatbot(_, style):
            style = style or {}
            style["display"] = "none" if style.get("display") == "block" else "block"
            return style
