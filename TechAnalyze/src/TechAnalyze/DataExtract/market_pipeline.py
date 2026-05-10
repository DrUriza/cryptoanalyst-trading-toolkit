import time
from ..DataExtract.MarketData.ib_connection import ib_connect, ib_disconnect
from ..DataExtract.MarketData.ib_orderbook  import extract_orderbook_snapshot, orderbook_raw_to_flat
from .MarketData.ib_fetcher                 import fetch_ib_m1
from ..DataExtract.MarketData.tf_builder    import build_tf

# ---- BANDERAS / ESTADO PARA HMI ----
IB_STATUS = {"orderbook_ok": False, "ib_last_ok_ts": 0.0}

class DataExtractPipeline:
    def __init__(self, paths, tf, tfids, ib_host = "127.0.0.1", ib_port = 7497, base_client_id = 1000):
        self.paths = paths
        self.tf = int(tf)
        self.tfids = tfids or {}
        self.ib_host = ib_host
        self.ib_port = ib_port
        self.base_client_id = base_client_id
    def _client_id_from_tf(self):
        return self.base_client_id + (self.tf // 60)
    def _resolve_client_id(self):
        return int(self.tfids.get(self.tf, self._client_id_from_tf()))
    def _ib_disconnect(self):
        ib_disconnect()
    def read_cfg1_asset(self):
        defaults = "BTC"
        obj = self.paths.manage_json(self.paths.CFG_FILE1, "read", default=defaults, create_if_missing=False)
        if not isinstance(obj, dict) or len(obj) == 0:
            return defaults
        asset = obj.get("asset") or defaults
        return str(asset)

    def run(self, capture_orderbook, bootstrap=False):
        asset = self.read_cfg1_asset()
        # -------- OrderBook (IB) --------
        if capture_orderbook:
            client_id = self._resolve_client_id()
            ob_flat = None
            try:
                ib = ib_connect(host=self.ib_host, port=self.ib_port, client_id=client_id)
                ob_raw = extract_orderbook_snapshot(asset, host=self.ib_host, port=self.ib_port, client_id=8000 + self.tf, rows=10, wait_s=1.2, retries=5)
                if ob_raw is None or ob_raw.empty:
                    IB_STATUS["orderbook_ok"] = False
                    print("⚠️ OrderBook vacío, se conserva el anterior")
                else:
                    ob_flat = orderbook_raw_to_flat(ob_raw)

                    if ob_flat is None or ob_flat.empty:
                        IB_STATUS["orderbook_ok"] = False
                        print("⚠️ OrderBook flat vacío, se conserva el anterior")
                    else:
                        entry = ob_flat.iloc[0].to_dict()
                        bid1 = entry.get("bid_price_1")
                        ask1 = entry.get("ask_price_1")
                        ok = True
                        if bid1 is not None and ask1 is not None and float(ask1) <= float(bid1):
                            ok = False
                            print(f"⚠️ Snapshot OB inválido (spread<=0) bid1={bid1} ask1={ask1} -> NO se guarda")
                        IB_STATUS["orderbook_ok"]  = ok
                        IB_STATUS["ib_last_ok_ts"] = time.time() if ok else IB_STATUS["ib_last_ok_ts"]
                        if ok:
                            entry["status"] = True
                            entry["tiempo"] = time.strftime("%Y-%m-%d %H:%M:%S")
                            self.paths.manage_json(self.paths.orderbook_flat_file(),mode="write",data=[entry])
            except Exception as e:
                IB_STATUS["orderbook_ok"] = False
                print(f"🟠 [WARN][IB] OB falló: {e}")
                self.paths.manage_json(self.paths.orderbook_flat_file(),mode="write",data=[{"status": False, "tiempo": time.strftime("%Y-%m-%d %H:%M:%S")}])
            finally:
                self._ib_disconnect()
                time.sleep(0.5)
        # -------- Market Data (MT5) --------
        df_m1 = fetch_ib_m1(asset,host=self.ib_host,port=self.ib_port,client_id=self._resolve_client_id(),lookback="6 D",bars=max(7500, 500 * max(1, self.tf // 60)))
        df_tf = build_tf(df_m1, self.tf // 60)
        self.paths.manage_json(self.paths.market_file(self.tf), mode="write", data=df_tf.to_dict(orient="records"))
