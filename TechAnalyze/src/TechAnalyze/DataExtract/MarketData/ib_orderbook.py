import re
import time
from datetime          import datetime
import pandas          as pd
from ib_insync         import IB, Crypto, Stock
from ib_insync.wrapper import Wrapper


# -------------------------------------------------
# PATCH LOCAL: ignorar updates corruptos de MktDepth
# -------------------------------------------------
_DEPTH_PATCHED = False

def _patch_ib_depth_noise():
    global _DEPTH_PATCHED
    if _DEPTH_PATCHED:
        return
    original_update_l2 = Wrapper.updateMktDepthL2
    original_update = Wrapper.updateMktDepth

    def safe_updateMktDepthL2(self, reqId, position, marketMaker, operation, side, price, size, isSmartDepth=False):
        try:
            return original_update_l2(
                self, reqId, position, marketMaker, operation, side, price, size, isSmartDepth
            )
        except IndexError:
            print("⚠️ Interactive Brokers: basura temporal en Market Depth ignorada.")
            return

    def safe_updateMktDepth(self, reqId, position, operation, side, price, size):
        try:
            return original_update(self, reqId, position, operation, side, price, size)
        except IndexError:
            print("⚠️ Interactive Brokers: basura temporal en Market Depth ignorada.")
            return

    Wrapper.updateMktDepthL2 = safe_updateMktDepthL2
    Wrapper.updateMktDepth = safe_updateMktDepth
    _DEPTH_PATCHED = True

_patch_ib_depth_noise()

# -------------------------------------------------
# RESOLVER CONTRATO SEGÚN ASSET
# -------------------------------------------------
def _resolve_depth_contract_candidates(asset: str):
    s = str(asset).upper().strip()

    # BTC / crypto
    if s in ("BTC", "BTCUSD"):
        return [Crypto("BTC", "PAXOS", "USD")]

    # Stocks / ETFs
    if s in ("AMZN", "AMAZON"):
        return [Stock("AMZN", "SMART", "USD")]

    if s in ("TSLA", "TESLA"):
        return [Stock("TSLA", "SMART", "USD")]

    if s in ("QQQ", "NASDAQ"):
        return [Stock("QQQ", "SMART", "USD")]

    if s in ("SLV", "SILVER", "SILVERETF"):
        return [Stock("SLV", "SMART", "USD")]

    # Compatibilidad por si luego agregas más
    if s in ("AAPL", "APPLE"):
        return [Stock("AAPL", "SMART", "USD")]

    raise ValueError(f"❌ Asset no soportado para Order Book: '{asset}'. "
                     f"Usa BTC, AMZN, TSLA, QQQ o SLV.")


def orderbook_raw_to_flat(df_raw):
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    flat = {}
    now = time.time()
    flat["ts"] = now
    flat["ts_iso"] = datetime.fromtimestamp(now).isoformat()

    cols = df_raw.columns
    levels = sorted(
        set(int(re.findall(r"\d+", c)[0]) for c in cols if "_" in c and re.findall(r"\d+", c))
    )

    for lvl in levels:
        flat[f"bid_price_{lvl}"] = df_raw.get(f"bid_price_{lvl}", [None])[0]
        flat[f"bid_qty_{lvl}"] = df_raw.get(f"bid_qty_{lvl}", [None])[0]
        flat[f"ask_price_{lvl}"] = df_raw.get(f"ask_price_{lvl}", [None])[0]
        flat[f"ask_qty_{lvl}"] = df_raw.get(f"ask_qty_{lvl}", [None])[0]

    return pd.DataFrame([flat]) if flat else pd.DataFrame()


def extract_orderbook_snapshot(asset, host="127.0.0.1", port=7497, client_id=9001, rows=10, wait_s=1.2, retries=4):
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=5)
        ib.sleep(0.5)
        candidates = _resolve_depth_contract_candidates(asset)
        for contract in candidates:
            ticker = None
            resolved_contract = contract
            try:
                qualified = ib.qualifyContracts(contract)
                if qualified:
                    resolved_contract = qualified[0]
                print(f"📘 OB asset={asset} contract={resolved_contract}")
                ticker = ib.reqMktDepth(resolved_contract, numRows=rows)
                for _ in range(retries):
                    ib.sleep(wait_s)
                    bids = [b for b in list(ticker.domBids) if getattr(b, "price", 0) and float(b.price) > 0]
                    asks = [a for a in list(ticker.domAsks) if getattr(a, "price", 0) and float(a.price) > 0]
                    bids = sorted(bids, key=lambda x: float(x.price), reverse=True)
                    asks = sorted(asks, key=lambda x: float(x.price))
                    if not bids or not asks:
                        continue
                    best_bid = float(bids[0].price)
                    best_ask = float(asks[0].price)
                    if best_ask <= best_bid:
                        continue
                    depth = min(len(bids), len(asks), rows)
                    if depth <= 0:
                        continue
                    result = {}
                    for i in range(depth):
                        lvl = i + 1
                        result[f"bid_price_{lvl}"] = float(bids[i].price)
                        result[f"bid_qty_{lvl}"] = float(bids[i].size)
                        result[f"ask_price_{lvl}"] = float(asks[i].price)
                        result[f"ask_qty_{lvl}"] = float(asks[i].size)
                    df = pd.DataFrame([result])
                    print(f"✅ OB recibido para {asset} con {depth} niveles")
                    return df
            except Exception as e:
                print(f"⚠️ Falló OB para {asset} con contract={resolved_contract}: {e}")
            finally:
                try:
                    if ticker is not None:
                        ib.cancelMktDepth(resolved_contract)
                        ib.sleep(0.2)
                except Exception:
                    pass
        print(f"⚠️ No se pudo obtener OB para {asset}")
        return pd.DataFrame()
    finally:
        try:
            if ib.isConnected():
                ib.disconnect()
        except Exception:
            pass