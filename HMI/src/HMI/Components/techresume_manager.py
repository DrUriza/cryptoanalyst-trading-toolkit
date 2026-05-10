# =====================================================
# Components/tech_resume_manager.py
# Dashboard de señales técnicas (TA_Resume + Volume)
# =====================================================
import os
from dash import html


class TechResumeManager:
    def __init__(self, summ_dir, paths):
        self.summary_dir = os.path.abspath(summ_dir)
        self.paths = paths

        # SOLO estos pueden ser GRAY cuando están en medio (neutral)
        self.GRAY_ALLOWED = {"BB-M", "WD"}

        # Si por alguna razón no viene Dir/Ten, NO quiero gris.
        self.DEFAULT_DIR_IF_UNKNOWN = +1  # +1 => green, -1 => red

    # =====================================================
    # LOAD LAST SUMMARY
    # =====================================================
    def load_last_summary(self, timeframe):
        fname = f"Summary_Data_{timeframe}s.json"
        path = os.path.join(self.summary_dir, fname)
        data = self.paths.manage_json(path, "read", default={})
        return data

    # =====================================================
    # HELPERS
    # =====================================================
    def _safe_float(self, x, default=0.0):
        try:
            return float(x)
        except Exception:
            return float(default)

    def _clamp01_100(self, x: float) -> float:
        # UI: solo 0..100
        if x < 0.0:
            return 0.0
        if x > 100.0:
            return 100.0
        return x

    def _extract_dir(self, d: dict) -> int:
        """
        Dirección SIEMPRE debe existir:
        1) Dir
        2) Ten
        3) SlopeSign
        4) DEFAULT_DIR_IF_UNKNOWN (nunca gris)
        """
        if not d:
            return int(self.DEFAULT_DIR_IF_UNKNOWN)

        for k in ("Dir", "Ten", "SlopeSign"):
            v = d.get(k, None)
            if v is None:
                continue
            try:
                vi = int(float(v))
                if vi > 0:
                    return +1
                if vi < 0:
                    return -1
            except Exception:
                pass

        return int(self.DEFAULT_DIR_IF_UNKNOWN)

    def _color_for_key(self, key: str, d: dict) -> str:
        """
        Regla:
        - Para TODO excepto BB-M y WD => NUNCA GRAY, se fuerza por dirección.
        - Para BB-M y WD => GRAY permitido si está neutral real (Dir/Ten=0 o Signal=NEUTRAL).
        """
        if not d:
            if key in self.GRAY_ALLOWED:
                return "gray"
            return "green" if self.DEFAULT_DIR_IF_UNKNOWN > 0 else "red"

        signal = (d.get("Signal") or "").upper()

        if key in self.GRAY_ALLOWED:
            # neutral real => gray permitido
            try:
                dirv = int(float(d.get("Dir", 0)))
            except Exception:
                dirv = 0
            try:
                tenv = int(float(d.get("Ten", 0)))
            except Exception:
                tenv = 0

            if signal == "NEUTRAL" or (dirv == 0 and tenv == 0):
                return "gray"

            # no neutral => fuerza por dirección
            dir_final = self._extract_dir(d)
            return "green" if dir_final > 0 else "red"

        # para el resto: SIEMPRE green/red
        dir_final = self._extract_dir(d)
        return "green" if dir_final > 0 else "red"

    def _arrow_from_dir(self, dirv: int) -> str:
        return "↑" if dirv > 0 else "↓"

    # =====================================================
    # MAIN TABLE
    # =====================================================
    def generate_signal_table(self, timeframe):
        last = self.load_last_summary(timeframe)
        if not last:
            return html.Div(f"No hay Summary_Data para {timeframe}s")

        ta = last.get("TA_Resume", {})
        if not ta:
            return html.Div("TA_Resume no disponible")

        high_vol = int(last.get("High_Volume", 0))

        indicators = {
            "BB-M": "BB- M",
            "ADX":  "ADX",
            "TSI":  "TSI",
            "RSI":  "RSI",
            "MA-S": "MA-S",
            "MA-E": "MA-E",
            "MA-N": "MA-N",
            "ATR":  "ATR",
            "WD":   "WD",
            "MACD": "MACD",
        }

        rows = []

        # ----------------------- BASE INDICATORS ----------------------------
        for key, label_name in indicators.items():
            d = ta.get(key, {}) or {}

            # FZA RAW: NO SE TOCA (puede ser >100, <0, lo que sea)
            fza_raw = self._safe_float(d.get("Fza", 0.0), 0.0)

            # UI: solo muestro magnitud 0..100 (debil => baja)
            fza_ui = self._clamp01_100(abs(fza_raw))

            # Tiempo/recencia: ese sí es 0..100
            fzat = self._clamp01_100(self._safe_float(d.get("FzaT", 0.0), 0.0))

            # Dirección SIEMPRE existe
            dir_final = self._extract_dir(d)
            color = self._color_for_key(key, d)

            # Flecha: solo si no es neutral gray
            if color == "gray":
                txt_main = f"{fza_ui:.1f}%"
            else:
                arr = self._arrow_from_dir(dir_final)
                txt_main = f"{arr} {fza_ui:.1f}%"

            arrow = html.Span([
                html.Span(
                    txt_main,
                    style={"color": color, "fontWeight": "bold", "fontSize": "10px"}
                ),
                html.Span(
                    f" [{fzat:.1f}%]",
                    style={"color": "black", "fontWeight": "bold", "fontSize": "10px"}
                )
            ])

            rows.append(
                html.Tr([
                    html.Td(label_name, style={"fontWeight": "bold", "fontSize": "10px"}),
                    html.Td(arrow, style={"textAlign": "center"})
                ])
            )

        # ======================= HIGH VOLUME ===========================
        rows.append(html.Tr([html.Td(colSpan=2, children=html.Hr())]))
        hv_span = (
            html.Span("HIGH VOLUME", style={"color": "orange", "fontWeight": "bold", "fontSize": "12px"})
            if high_vol
            else html.Span("Normal Volume", style={"color": "gray", "fontSize": "11px"})
        )

        rows.append(
            html.Tr([
                html.Td("VOL ALERT", style={"fontWeight": "bold", "fontSize": "11px"}),
                html.Td(hv_span, style={"textAlign": "center"})
            ])
        )

        # ======================= STOCHASTIC ===========================
        rows.append(html.Tr([html.Td(colSpan=2, children=html.Hr())]))
        for key in ["STK", "STKs"]:
            d = ta.get(key, {}) or {}
            if not d:
                continue

            fza_raw = self._safe_float(d.get("Fza", 0.0), 0.0)
            fza_ui = self._clamp01_100(abs(fza_raw))

            dir_final = self._extract_dir(d)
            color = self._color_for_key(key, d)
            arr = self._arrow_from_dir(dir_final)

            txt = f"{arr} {fza_ui:.3f}%"

            rows.append(
                html.Tr([
                    html.Td(key, style={"fontWeight": "bold", "fontSize": "11px"}),
                    html.Td(
                        html.Span(txt, style={"color": color, "fontWeight": "bold", "fontSize": "11px"}),
                        style={"textAlign": "center"}
                    )
                ])
            )

        # ======================= RESUMEN FINAL ===========================
        rows.append(html.Tr([html.Td(colSpan=2, children=html.Hr())]))
        final_keys = {"MA-E": "Prom. MM", "ADX": "Tendencia"}
        for key, label in final_keys.items():
            d = ta.get(key, {}) or {}
            if not d:
                continue

            fza_raw = self._safe_float(d.get("Fza", 0.0), 0.0)
            fza_ui = self._clamp01_100(abs(fza_raw))

            dir_final = self._extract_dir(d)
            color = self._color_for_key(key, d)
            arr = self._arrow_from_dir(dir_final)

            txt = f"{arr} {fza_ui:.3f}%"

            rows.append(
                html.Tr([
                    html.Td(label, style={"fontWeight": "bold", "fontSize": "12px"}),
                    html.Td(
                        html.Span(txt, style={"color": color, "fontWeight": "bold", "fontSize": "12px"}),
                        style={"textAlign": "center"}
                    )
                ])
            )

        # ======================= TABLE ===========================
        return html.Table(
            [html.Tr([
                html.Th(
                    f"Tech Resume {timeframe}s",
                    colSpan=2,
                    style={"fontSize": "14px", "padding": "6px", "textAlign": "center"}
                )
            ])] + rows,
            style={
                "fontSize": "12px",
                "margin": "10px auto",
                "borderSpacing": "6px",
                "border": "1px solid #ccc",
                "minWidth": "220px"
            }
        )