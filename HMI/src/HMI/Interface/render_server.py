# =====================================================
# Interface/render_server.py
# Servidor Flask auxiliar para /plot/<id>
# Compatible con RadioItems y PlotManager actual
# =====================================================

import os
import uuid
import threading
import webbrowser
import flask
from dash import Dash


class RenderServer:
    def __init__(self, plot_manager, port=8055):
        self.plot_mgr = plot_manager
        self.port = port
        self.plots_data = {}
        self._lock = False

    # -------------------------------------------------
    # Registrar rutas Flask (NO callbacks Dash)
    # -------------------------------------------------
    def register_routes(self, app: Dash):

        @app.server.route("/plot/<plot_id>")
        def serve_plot(plot_id):
            if plot_id not in self.plots_data:
                return "Invalid Plot ID", 404

            info = self.plots_data[plot_id]

            fig = self.plot_mgr.build_single_plot(
                plot_type=info["plot_type"],
                asset=info["asset"],
                zoom=info["zoom"],
                data_source=info["source"],
            )

            return flask.render_template_string(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8"/>
                    <title>Elatin Plot</title>
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                </head>
                <body style="margin:0;">
                    <div id="plot" style="width:100vw;height:100vh;"></div>
                    <script>
                        const fig = {{ fig | safe }};
                        Plotly.newPlot(
                            "plot",
                            fig.data,
                            fig.layout,
                            {responsive: true}
                        );
                    </script>
                </body>
                </html>
                """,
                fig=fig.to_json(),
            )

    # -------------------------------------------------
    # Abrir gráfica externa (helper)
    # -------------------------------------------------
    def open_external_plot(self, plot_type, asset, zoom, source):
        plot_id = str(uuid.uuid4())[:8]
        self.plots_data[plot_id] = {"plot_type": plot_type,
                                    "asset": asset,
                                    "zoom": zoom,
                                    "source": source}
        url = f"http://127.0.0.1:{self.port}/plot/{plot_id}"
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()

# =====================================================
# Browser Controller (abre app solo una vez)
# =====================================================
class BrowserController:
    def __init__(self, port=8055):
        self.port = port
        self.lock_file = f".browser_lock_{port}"
    def open_browser(self):
        if not os.path.exists(self.lock_file):
            webbrowser.open(f"http://127.0.0.1:{self.port}/")
            with open(self.lock_file, "w") as f:
                f.write("opened")
