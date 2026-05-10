# =====================================================
# Components/orderbook_manager.py
# OrderBook INDEPENDIENTE (Flat + Metrics + States)
# =====================================================
import os
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, dash_table


class OrderBookManager:
    def __init__(self, orderbook_dir, paths):
        self.orderbook_dir = os.path.abspath(orderbook_dir)
        self.paths = paths

        # Stale threshold (segundos) para marcar "Ob Stale"
        self.STALE_S = 120

        # Umbral para marcar "Desfase" (USD)
        self.DESFASE_TH = 0.50

        # Thresholds de lectura visual (ratio), solo UI
        self.PRESS_BUY_TH = 1.10
        self.PRESS_SELL_TH = 0.90
        self.IMB_BUY_TH = 0.55
        self.IMB_SELL_TH = 0.45

        # Anti-trampas extra (UI)
        self.SPREAD_USD_TH = 10.0         # spread absoluto grande
        self.SPREAD_PCT_TH = 0.0008       # 8 bps del mid
        self.TOP_HEAVY_TH = 0.85          # L2/(L10) alto
        self.FLIP_CHANGES_TH = 3          # cambios de señal en últimos 5

    # =====================================================
    # LOADERS
    # =====================================================
    def _load_flat(self):
        path = os.path.join(self.orderbook_dir, "OrderBook_Flat.json")
        data = self.paths.manage_json(path, "read", default=[])
        return data if isinstance(data, list) else []

    def _load_metrics(self):
        path = os.path.join(self.orderbook_dir, "OrderBook_Metrics.json")
        data = self.paths.manage_json(path, "read", default={})
        return data if isinstance(data, dict) else {}

    def _load_states(self):
        path = os.path.join(self.orderbook_dir, "OrderBook_States.json")
        data = self.paths.manage_json(path, "read", default=[])
        return data if isinstance(data, list) else []

    # =====================================================
    # HELPERS
    # =====================================================
    @staticmethod
    def _fmt_num(x, nd=2):
        try:
            if x is None:
                return "-"
            return f"{float(x):.{nd}f}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_sign(x, nd=2):
        try:
            v = float(x)
            s = "+" if v >= 0 else ""
            return f"{s}{v:.{nd}f}"
        except Exception:
            return "0.00"

    @staticmethod
    def _safe_float(x):
        try:
            return float(x)
        except Exception:
            return None

    @staticmethod
    def _hhmmss_from_any(ts_iso=None, tiempo=None, ts=None):
        """
        Devuelve HH:MM:SS
        """
        try:
            if isinstance(tiempo, str) and len(tiempo) >= 19:
                return tiempo[-8:]
            if isinstance(ts_iso, str) and "T" in ts_iso:
                return ts_iso.split("T")[1].split(".")[0]
            if ts is not None:
                return datetime.fromtimestamp(float(ts)).strftime("%H:%M:%S")
        except Exception:
            pass
        return "--:--:--"

    def _flat_entry(self):
        flat = self._load_flat()
        if not flat:
            return None
        return flat[-1] if isinstance(flat[-1], dict) else None

    def _signal_theme(self, signal: str):
        s = (signal or "NEUTRAL").upper()
        if s == "BUY":
            return {"col": "#0a7a25", "bg": "rgba(10,122,37,0.08)", "bd": "rgba(10,122,37,0.35)"}
        if s == "SELL":
            return {"col": "#b00020", "bg": "rgba(176,0,32,0.08)", "bd": "rgba(176,0,32,0.35)"}
        return {"col": "#555", "bg": "rgba(0,0,0,0.03)", "bd": "rgba(0,0,0,0.10)"}

    def _badge(self, text, color="#666", bg="rgba(0,0,0,0.03)", bd="rgba(0,0,0,0.15)"):
        return html.Span(
            text,
            style={
                "border": f"1px solid {bd}",
                "color": color,
                "background": bg,
                "padding": "6px 12px",
                "borderRadius": "16px",
                "fontSize": "12px",
                "fontWeight": "bold",
                "whiteSpace": "nowrap"
            }
        )

    def _metric_card(self, title, value_big, subtitle, theme, value_color=None):
        return html.Div(
            [
                html.Div(title, style={"fontSize": "13px", "color": "#333", "marginBottom": "6px", "fontWeight": "bold"}),
                html.Div(value_big, style={"fontSize": "34px", "fontWeight": "bold", "color": value_color or "#111"}),
                html.Div(subtitle, style={"fontSize": "12px", "color": theme["col"], "marginTop": "6px"})
            ],
            style={
                "border": f"1px solid {theme['bd']}",
                "background": theme["bg"] if theme else "white",
                "borderRadius": "16px",
                "padding": "14px 16px",
                "boxShadow": "0 2px 10px rgba(0,0,0,0.04)"
            }
        )

    def _value_color_pressure(self, p_ratio):
        """
        Colorea usando RATIO (no score):
          ratio >= 1.10 => BUY (verde)
          ratio <= 0.90 => SELL (rojo)
        """
        p = self._safe_float(p_ratio)
        if p is None:
            return "#111"
        if p >= self.PRESS_BUY_TH:
            return "#0a7a25"
        if p <= self.PRESS_SELL_TH:
            return "#b00020"
        return "#555"

    def _value_color_imbalance(self, im):
        im = self._safe_float(im)
        if im is None:
            return "#111"
        if im >= self.IMB_BUY_TH:
            return "#0a7a25"
        if im <= self.IMB_SELL_TH:
            return "#b00020"
        return "#555"

    # =====================================================
    # PRESSURE TRANSFORM (ratio -> signed score)
    # =====================================================
    def _pressure_to_score(self, p, eps=1e-12):
        """
        Convierte ratio pressure p a score firmado:
          p=1   -> 0
          p>1   -> +(p-1)
          p<1   -> -(1/p - 1)  (venta fuerte => muy negativo)
        """
        try:
            p = float(p)
        except Exception:
            return 0.0

        if p <= eps:
            # evita blow-up infinito, pero conserva "muy negativo"
            return -1e6

        if p >= 1.0:
            return p - 1.0
        return -(1.0 / p - 1.0)

    # =====================================================
    # CORE CALCS (desde FLAT)
    # =====================================================
    def _calc_liq_best(self, entry: dict, levels: int = 10):
        bids = []
        asks = []
        bid_liq = 0.0
        ask_liq = 0.0

        for i in range(1, levels + 1):
            bp = self._safe_float(entry.get(f"bid_price_{i}"))
            bq = self._safe_float(entry.get(f"bid_qty_{i}"))
            ap = self._safe_float(entry.get(f"ask_price_{i}"))
            aq = self._safe_float(entry.get(f"ask_qty_{i}"))

            if bp is not None and bq is not None:
                bids.append(bp)
                bid_liq += bq
            if ap is not None and aq is not None:
                asks.append(ap)
                ask_liq += aq

        if not bids or not asks:
            return None

        best_bid = max(bids)
        best_ask = min(asks)
        spread = best_ask - best_bid
        mid = (best_bid + best_ask) / 2.0

        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": mid,
            "spread": spread,
            "bid_liq": bid_liq,
            "ask_liq": ask_liq
        }

    def _calc_pressure(self, entry: dict, levels: int = 10):
        m = self._calc_liq_best(entry, levels=levels)
        if not m:
            return None
        if m["bid_liq"] > 0 and m["ask_liq"] > 0:
            return m["bid_liq"] / m["ask_liq"]
        return None

    def _calc_imbalance(self, entry: dict, levels: int = 10):
        m = self._calc_liq_best(entry, levels=levels)
        if not m:
            return None
        tot = m["bid_liq"] + m["ask_liq"]
        if tot > 0:
            return m["bid_liq"] / tot
        return None

    def _compute_bias_and_flags(self, p_l10, imb_l10, state_sig, l2_spread, l2_mid, bid_liq_l2, ask_liq_l2, bid_liq_l10, ask_liq_l10, last5_states):
        """
        Anti-trampas UI (sesgo y alertas) usando ratio/imbalance.
        """
        state_sig = (state_sig or "NEUTRAL").upper()

        # --- Sesgo por Pressure (ratio)
        press_side = "NEUTRAL"
        if p_l10 is not None:
            if p_l10 >= self.PRESS_BUY_TH:
                press_side = "BUY"
            elif p_l10 <= self.PRESS_SELL_TH:
                press_side = "SELL"

        # --- Sesgo por Imbalance
        imb_side = "NEUTRAL"
        if imb_l10 is not None:
            if imb_l10 >= self.IMB_BUY_TH:
                imb_side = "BUY"
            elif imb_l10 <= self.IMB_SELL_TH:
                imb_side = "SELL"

        # --- Conflicto
        conflict = False
        if press_side != "NEUTRAL" and imb_side != "NEUTRAL" and press_side != imb_side:
            conflict = True

        # --- Sesgo final
        if conflict:
            bias = "NEUTRAL"
        else:
            bias = press_side if press_side != "NEUTRAL" else imb_side

        # --- Mismatch State vs Sesgo
        mismatch = False
        if bias != "NEUTRAL" and state_sig != "NEUTRAL" and bias != state_sig:
            mismatch = True

        # --- Spread flags
        spread_invalid = False
        spread_wide = False
        if l2_spread is not None:
            if float(l2_spread) <= 0:
                spread_invalid = True
            else:
                if float(l2_spread) >= self.SPREAD_USD_TH:
                    spread_wide = True
                if l2_mid is not None and float(l2_mid) > 0:
                    if (float(l2_spread) / float(l2_mid)) >= self.SPREAD_PCT_TH:
                        spread_wide = True

        # --- Top-heavy (L2 concentra casi todo)
        top_heavy = False
        try:
            l2_tot = (float(bid_liq_l2 or 0.0) + float(ask_liq_l2 or 0.0))
            l10_tot = (float(bid_liq_l10 or 0.0) + float(ask_liq_l10 or 0.0))
            if l10_tot > 0:
                ratio = l2_tot / l10_tot
                if ratio >= self.TOP_HEAVY_TH:
                    top_heavy = True
        except Exception:
            pass

        # --- Flip-flop (últimos 5 states)
        flip_flop = False
        try:
            sigs = [(x.get("signal") or "NEUTRAL").upper() for x in (last5_states or []) if isinstance(x, dict)]
            changes = 0
            for i in range(1, len(sigs)):
                if sigs[i] != sigs[i - 1]:
                    changes += 1
            if changes >= self.FLIP_CHANGES_TH:
                flip_flop = True
        except Exception:
            pass

        return {
            "bias": bias,
            "press_side": press_side,
            "imb_side": imb_side,
            "conflict": conflict,
            "mismatch": mismatch,
            "spread_invalid": spread_invalid,
            "spread_wide": spread_wide,
            "top_heavy": top_heavy,
            "flip_flop": flip_flop
        }

    # =====================================================
    # TABLE
    # =====================================================
    def get_table(self, levels=20):
        entry = self._flat_entry()
        if not entry:
            return pd.DataFrame()

        rows = []
        for i in range(1, levels + 1):
            bp = entry.get(f"bid_price_{i}")
            bq = entry.get(f"bid_qty_{i}")
            ap = entry.get(f"ask_price_{i}")
            aq = entry.get(f"ask_qty_{i}")
            if None in (bp, bq, ap, aq):
                continue
            try:
                rows.append({
                    "Bid Price": f"{float(bp):.2f}",
                    "Bid Qty":   f"{float(bq):.6f}",
                    "Ask Price": f"{float(ap):.2f}",
                    "Ask Qty":   f"{float(aq):.6f}",
                })
            except Exception:
                continue

        return pd.DataFrame(rows)

    # =====================================================
    # PRESSURE HISTORY (STATES)  --- ahora grafica SCORE
    # =====================================================
    def get_pressure_figure(self, max_points=100):
        states = self._load_states()
        if not states:
            return None, "⚠ Sin OrderBook_States.json"

        states = [s for s in states if isinstance(s, dict) and s.get("pressure") is not None and s.get("time")]
        if not states:
            return None, "⚠ States sin pressure/time"

        states = states[-max_points:]
        x = [s.get("time", "--:--:--") for s in states]
        y = [self._pressure_to_score(s.get("pressure", 1.0)) for s in states]

        def sig_col(sig):
            sig = (sig or "NEUTRAL").upper()
            if sig == "BUY":
                return "#0a7a25"
            if sig == "SELL":
                return "#b00020"
            return "#777"

        point_cols = [sig_col(s.get("signal")) for s in states]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines+markers",
            name="PressureScore",
            marker=dict(color=point_cols, size=7),
            line=dict(width=2, color="#777")
        ))

        # Línea neutral
        fig.add_hline(y=0, line_dash="dash", line_width=1, line_color="#999")

        fig.update_layout(
            height=320,
            margin=dict(t=40, b=30, l=30, r=20),
            title="Pressure Score (States)",
            showlegend=False
        )
        return fig, None

    # =====================================================
    # DEPTH
    # =====================================================
    def get_depth_figure(self, levels=20):
        entry = self._flat_entry()
        if not entry:
            return None, "⚠ Sin OrderBook_Flat.json"

        bids = []
        asks = []

        for i in range(1, levels + 1):
            bp = entry.get(f"bid_price_{i}")
            bq = entry.get(f"bid_qty_{i}")
            ap = entry.get(f"ask_price_{i}")
            aq = entry.get(f"ask_qty_{i}")

            try:
                if bp is not None and bq is not None:
                    bids.append((float(bp), float(bq)))
                if ap is not None and aq is not None:
                    asks.append((float(ap), float(aq)))
            except Exception:
                pass

        if not bids or not asks:
            return None, "⚠ Profundidad incompleta"

        bids = sorted(bids, key=lambda x: x[0])  # low -> high
        asks = sorted(asks, key=lambda x: x[0])  # low -> high

        bid_px, bid_q = zip(*bids)
        ask_px, ask_q = zip(*asks)

        bid_cum = pd.Series(list(bid_q)[::-1]).cumsum()[::-1]
        ask_cum = pd.Series(list(ask_q)).cumsum()

        best_bid = max(bid_px)
        best_ask = min(ask_px)

        if best_ask <= best_bid:
            return None, f"⚠ Spread inválido: best_bid={best_bid:.2f} best_ask={best_ask:.2f}"

        mid = (best_bid + best_ask) / 2.0

        left_span = mid - min(bid_px)
        right_span = max(ask_px) - mid
        half_span = max(left_span, right_span) * 1.08
        x0, x1 = mid - half_span, mid + half_span

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=bid_px, y=bid_cum, mode="lines", name="Bids",
            line=dict(color="#0a7a25"), line_shape="hv"
        ))
        fig.add_trace(go.Scatter(
            x=ask_px, y=ask_cum, mode="lines", name="Asks",
            line=dict(color="#b00020"), line_shape="hv"
        ))
        fig.add_vline(x=mid, line_dash="dash", annotation_text="Mid", annotation_position="top")

        fig.update_layout(
            height=320,
            margin=dict(t=40, b=30, l=30, r=20),
            title="Market Depth",
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        )
        fig.update_xaxes(range=[x0, x1], autorange=False)
        return fig, None

    # =====================================================
    # STATES (SIGNAL + HISTORY)
    # =====================================================
    def _get_state_pack(self):
        states = self._load_states()
        if not states:
            return {"signal": "NEUTRAL", "pressure": None, "last5": [], "time": "--:--:--"}

        last = states[-1] if isinstance(states[-1], dict) else {}
        last5 = [x for x in states[-5:] if isinstance(x, dict)]
        return {
            "signal": (last.get("signal") or "NEUTRAL").upper(),
            "pressure": last.get("pressure"),
            "time": last.get("time") or "--:--:--",
            "last5": last5
        }

    def _signal_badge(self, sig):
        sig = (sig or "NEUTRAL").upper()
        if sig == "BUY":
            return html.Span("📈 BUY", style={"color": "#0a7a25", "fontWeight": "bold"})
        if sig == "SELL":
            return html.Span("📉 SELL", style={"color": "#b00020", "fontWeight": "bold"})
        return html.Span("⚖️ NEUTRAL", style={"color": "#666", "fontWeight": "bold"})

    def _states_chips(self, items):
        if not items:
            return html.Div("• Sin historial")

        chips = []
        for x in items:
            sig = (x.get("signal") or "NEUTRAL").upper()
            pres_ratio = x.get("pressure")
            pres_score = self._pressure_to_score(pres_ratio)
            t = x.get("time", "--:--:--")
            theme = self._signal_theme(sig)

            chips.append(
                html.Div(
                    f"{t} | {sig} | {self._fmt_num(pres_score, 3)}",
                    style={
                        "border": f"1px solid {theme['bd']}",
                        "color": theme["col"],
                        "background": "white",
                        "padding": "6px 10px",
                        "borderRadius": "16px",
                        "fontSize": "12px",
                        "fontWeight": "bold",
                        "whiteSpace": "nowrap"
                    }
                )
            )

        return html.Div(
            chips,
            style={"display": "flex", "gap": "8px", "justifyContent": "center", "flexWrap": "wrap"}
        )

    # =====================================================
    # RENDER
    # =====================================================
    def render(self, asset, table_levels=20, depth_levels=20):
        entry = self._flat_entry()
        metrics = self._load_metrics()
        st = self._get_state_pack()

        theme = self._signal_theme(st["signal"])

        # ---- tiempos SOLO HH:MM:SS ----
        flat_time = "--:--:--"
        flat_ts = None
        flat_status = None
        if entry:
            flat_time = self._hhmmss_from_any(entry.get("ts_iso"), entry.get("tiempo"), entry.get("ts"))
            flat_ts = entry.get("ts")
            flat_status = entry.get("status")

        state_time = st.get("time", "--:--:--")

        # ---- stale ----
        age_s = None
        if flat_ts is not None:
            try:
                age_s = max(0.0, time.time() - float(flat_ts))
            except Exception:
                age_s = None
        is_stale = (age_s is not None and age_s > self.STALE_S)

        # ---- L2 / L10 desde FLAT ----
        l2 = self._calc_liq_best(entry, levels=2) if entry else None
        l10 = self._calc_liq_best(entry, levels=10) if entry else None
        if not l2 and l10:
            l2 = l10

        l2_bid = l2["best_bid"] if l2 else None
        l2_ask = l2["best_ask"] if l2 else None
        l2_mid = l2["mid"] if l2 else None
        l2_spread = l2["spread"] if l2 else None

        bid_liq_l2 = l2["bid_liq"] if l2 else None
        ask_liq_l2 = l2["ask_liq"] if l2 else None
        bid_liq_l10 = l10["bid_liq"] if l10 else None
        ask_liq_l10 = l10["ask_liq"] if l10 else None

        # Pressure / Imbalance
        p_ratio = self._safe_float(st.get("pressure"))
        p_score = self._pressure_to_score(p_ratio)

        p_l2 = self._calc_pressure(entry, levels=2) if entry else None
        p_l10 = self._calc_pressure(entry, levels=10) if entry else None
        imb_l10 = self._calc_imbalance(entry, levels=10) if entry else None

        # Metrics file (puede estar desfasado)
        m_bid = metrics.get("ob_best_bid")
        m_ask = metrics.get("ob_best_ask")
        m_mid = metrics.get("ob_mid_price")
        m_spread = metrics.get("ob_spread")

        # Desfase = L2 - Metrics
        d_bid = None
        d_ask = None
        if l2_bid is not None and m_bid is not None:
            try:
                d_bid = float(l2_bid) - float(m_bid)
            except Exception:
                pass
        if l2_ask is not None and m_ask is not None:
            try:
                d_ask = float(l2_ask) - float(m_ask)
            except Exception:
                pass

        # ---- Anti-trampas (Sesgo + alertas) ----
        bias_pack = self._compute_bias_and_flags(
            p_l10=p_l10,
            imb_l10=imb_l10,
            state_sig=st["signal"],
            l2_spread=l2_spread,
            l2_mid=l2_mid,
            bid_liq_l2=bid_liq_l2,
            ask_liq_l2=ask_liq_l2,
            bid_liq_l10=bid_liq_l10,
            ask_liq_l10=ask_liq_l10,
            last5_states=st["last5"]
        )
        bias = bias_pack["bias"]
        bias_theme = self._signal_theme(bias)

        bias_bad = self._badge(
            f"Sesgo: {bias}",
            color=bias_theme["col"],
            bg=bias_theme["bg"],
            bd=bias_theme["bd"]
        )

        alert_badges = []
        if bias_pack["conflict"]:
            alert_badges.append(self._badge(
                "Alerta: Conflicto (Pressure vs Imbalance)",
                color="#b00020", bg="rgba(176,0,32,0.08)", bd="rgba(176,0,32,0.35)"
            ))
        if bias_pack["mismatch"]:
            alert_badges.append(self._badge(
                "Alerta: Mismatch (State vs Sesgo)",
                color="#b00020", bg="rgba(176,0,32,0.08)", bd="rgba(176,0,32,0.35)"
            ))
        if bias_pack["spread_invalid"]:
            alert_badges.append(self._badge(
                "Alerta: Spread Inválido",
                color="#b00020", bg="rgba(176,0,32,0.08)", bd="rgba(176,0,32,0.35)"
            ))
        elif bias_pack["spread_wide"]:
            alert_badges.append(self._badge(
                "Alerta: Spread Alto",
                color="#b00020", bg="rgba(176,0,32,0.08)", bd="rgba(176,0,32,0.35)"
            ))
        if bias_pack["top_heavy"]:
            alert_badges.append(self._badge(
                "Alerta: Top-Heavy (L2 domina L10)",
                color="#b00020", bg="rgba(176,0,32,0.08)", bd="rgba(176,0,32,0.35)"
            ))
        if bias_pack["flip_flop"]:
            alert_badges.append(self._badge(
                "Alerta: Flip-Flop (Señal inestable)",
                color="#b00020", bg="rgba(176,0,32,0.08)", bd="rgba(176,0,32,0.35)"
            ))

        # ---- Badges base ----
        if d_bid is not None and d_ask is not None:
            bad = (abs(d_bid) > self.DESFASE_TH) or (abs(d_ask) > self.DESFASE_TH)
            desfase_bad = self._badge(
                f"Desfase (Best_Bid Δ={self._fmt_sign(d_bid, 2)} | Best_Ask Δ={self._fmt_sign(d_ask, 2)})",
                color="#b00020" if bad else "#0a7a25",
                bg="rgba(176,0,32,0.08)" if bad else "rgba(10,122,37,0.08)",
                bd="rgba(176,0,32,0.35)" if bad else "rgba(10,122,37,0.35)"
            )
        else:
            desfase_bad = self._badge("Desfase (N/A)", color="#666")

        ok = bool(flat_status) if flat_status is not None else False
        ob_ok_bad = self._badge(
            "Ob Ok" if ok else "Ob Fail",
            color="#0a7a25" if ok else "#b00020",
            bg="rgba(10,122,37,0.08)" if ok else "rgba(176,0,32,0.08)",
            bd="rgba(10,122,37,0.35)" if ok else "rgba(176,0,32,0.35)"
        )

        ob_stale_bad = self._badge(
            "Ob Stale" if is_stale else "Ob Fresh",
            color="#b00020" if is_stale else "#0a7a25",
            bg="rgba(176,0,32,0.08)" if is_stale else "rgba(10,122,37,0.08)",
            bd="rgba(176,0,32,0.35)" if is_stale else "rgba(10,122,37,0.35)"
        )

        using_bad = self._badge("Usando L2", color=theme["col"], bg=theme["bg"], bd=theme["bd"])

        # ---- figs ----
        fig_pressure, err_p = self.get_pressure_figure(max_points=100)
        fig_depth, err_d = self.get_depth_figure(levels=depth_levels)

        # ---- table ----
        table_df = self.get_table(levels=table_levels)

        # ===================== CARDS =====================
        cards = []

        cards.append(self._metric_card(
            "Best Bid",
            self._fmt_num(l2_bid, 2),
            f"L2={self._fmt_num(l2_bid,2)} | Metrics={self._fmt_num(m_bid,2)}",
            theme
        ))
        cards.append(self._metric_card(
            "Best Ask",
            self._fmt_num(l2_ask, 2),
            f"L2={self._fmt_num(l2_ask,2)} | Metrics={self._fmt_num(m_ask,2)}",
            theme
        ))
        cards.append(self._metric_card(
            "Mid",
            self._fmt_num(l2_mid, 2),
            f"L2={self._fmt_num(l2_mid,2)} | Metrics={self._fmt_num(m_mid,2)}",
            theme
        ))
        cards.append(self._metric_card(
            "Spread",
            self._fmt_num(l2_spread, 2),
            f"L2={self._fmt_num(l2_spread,2)} | Metrics={self._fmt_num(m_spread,2)}",
            theme
        ))
        cards.append(self._metric_card(
            "Imbalance",
            self._fmt_num(imb_l10, 3),
            "L10=Bid_Liq/(Bid+Ask)",
            theme,
            value_color=self._value_color_imbalance(imb_l10)
        ))

        # IMPORTANT: mostrar SCORE, colorear por RATIO
        cards.append(self._metric_card(
            "Pressure",
            self._fmt_num(p_score, 3),
            f"Score={self._fmt_num(p_score,3)} | Ratio={self._fmt_num(p_ratio,3)} | L2={self._fmt_num(p_l2,3)} | L10={self._fmt_num(p_l10,3)}",
            theme,
            value_color=self._value_color_pressure(p_ratio)
        ))

        cards.append(self._metric_card(
            "Bid Liq (L2/L10)",
            f"{self._fmt_num(bid_liq_l2,6)} / {self._fmt_num(bid_liq_l10,6)}",
            "Suma Qty",
            theme
        ))
        cards.append(self._metric_card(
            "Ask Liq (L2/L10)",
            f"{self._fmt_num(ask_liq_l2,6)} / {self._fmt_num(ask_liq_l10,6)}",
            "Suma Qty",
            theme
        ))

        # ===================== RENDER =====================
        return html.Div([
            html.H3(
                f"📊 OrderBook | {asset}",
                style={
                    "textAlign": "center",
                    "fontWeight": "bold",
                    "fontSize": "26px",
                    "marginBottom": "6px",
                    "color": "#111"
                }
            ),

            html.Div(
                self._signal_badge(st["signal"]),
                style={"textAlign": "center", "fontSize": "28px", "marginBottom": "10px"}
            ),

            html.Div(self._states_chips(st["last5"]), style={"marginBottom": "10px"}),

            html.Div([
                html.Div([
                    self._badge(f"Ob Flat: {flat_time}", color="#333", bg="rgba(0,0,0,0.03)", bd="rgba(0,0,0,0.12)"),
                    self._badge(f"Ob State: {state_time}", color="#333", bg="rgba(0,0,0,0.03)", bd="rgba(0,0,0,0.12)"),
                ], style={"display": "flex", "gap": "10px", "alignItems": "center"}),

                html.Div([
                    bias_bad,
                    desfase_bad,
                    ob_ok_bad,
                    ob_stale_bad,
                    using_bad
                ], style={"display": "flex", "gap": "10px", "alignItems": "center", "justifyContent": "flex-end", "flexWrap": "wrap"})

            ], style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "10px",
                "alignItems": "center",
                "marginBottom": "8px"
            }),

            html.Div(
                alert_badges if alert_badges else [self._badge("Alertas: Ninguna", color="#0a7a25", bg="rgba(10,122,37,0.08)", bd="rgba(10,122,37,0.35)")],
                style={"display": "flex", "gap": "10px", "justifyContent": "center", "flexWrap": "wrap", "marginBottom": "12px"}
            ),

            html.Div(
                cards,
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, 1fr)",
                    "gap": "14px",
                    "marginBottom": "14px"
                }
            ),

            html.Hr(),

            html.Div([
                html.Div([
                    dcc.Graph(
                        figure=fig_pressure,
                        config={"displayModeBar": False},
                        style={"height": "340px", "width": "100%"}
                    ) if fig_pressure else html.Div(err_p)
                ], style={"padding": "6px", "borderRadius": "14px", "border": f"1px solid {theme['bd']}"}),

                html.Div([
                    dcc.Graph(
                        figure=fig_depth,
                        config={"displayModeBar": False},
                        style={"height": "340px", "width": "100%"}
                    ) if fig_depth else html.Div(err_d)
                ], style={"padding": "6px", "borderRadius": "14px", "border": f"1px solid {theme['bd']}"}),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "18px",
                "alignItems": "start",
                "marginBottom": "18px"
            }),

            html.Div([
                html.H4(
                    "📘 OrderBook (Bid / Ask)",
                    style={
                        "textAlign": "center",
                        "fontSize": "18px",
                        "fontWeight": "bold",
                        "marginBottom": "8px"
                    }
                ),
                dash_table.DataTable(
                    columns=[{"name": c, "id": c} for c in table_df.columns],
                    data=table_df.to_dict("records"),
                    page_action="none",
                    style_table={
                        "width": "100%",
                        "maxWidth": "720px",
                        "margin": "0 auto",
                        "height": "380px",
                        "overflowY": "auto",
                        "borderRadius": "14px",
                        "border": "1px solid rgba(0,0,0,0.10)"
                    },
                    style_cell={
                        "textAlign": "center",
                        "fontSize": "11px",
                        "padding": "6px",
                        "whiteSpace": "nowrap"
                    },
                    style_header={
                        "fontWeight": "bold",
                        "backgroundColor": "#f2f2f2"
                    },
                )
            ], style={"padding": "10px"})
        ], style={"marginTop": "10px"})