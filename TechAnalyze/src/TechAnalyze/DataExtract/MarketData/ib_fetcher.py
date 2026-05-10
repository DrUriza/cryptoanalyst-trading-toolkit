import pandas       as pd
from ib_insync      import Forex, Crypto, Stock, CFD, util
from .ib_connection import ib_connect, ib_disconnect


# =============================
# 1) RESOLVER CONTRATO IB
# =============================
def _resolve_contract(symbol):
    s = str(symbol).upper().strip()

    # -------- CRYPTO --------
    if s in ("BTC", "BTCUSD"):
        return Crypto("BTC", "PAXOS", "USD")

    # -------- STOCKS / ETF --------
    if s in ("TSLA", "TESLA"):
        return Stock("TSLA", "SMART", "USD")

    if s in ("AMZN", "AMAZON"):
        return Stock("AMZN", "SMART", "USD")

    # NASDAQ por ETF
    if s in ("QQQ", "NASDAQ"):
        return Stock("QQQ", "SMART", "USD")

    # -------- SILVER --------
    # ETF de plata
    if s in ("SLV", "SILVER", "SILVERETF"):
        return Stock("SLV", "SMART", "USD")

    # -------- FOREX --------
    if len(s) == 3 and s.isalpha():
        return Forex(f"{s}USD")

    if len(s) == 6 and s.isalpha():
        return Forex(s)

    raise ValueError(f"❌ Símbolo no soportado o ambiguo: '{symbol}'. "
                     f"Usa uno explícito como BTC, TSLA, AMZN, QQQ, SLV.")


# =============================
# 2) RESOLVER whatToShow
# =============================
def _resolve_what_to_show(symbol: str):
    s = str(symbol).upper().strip()

    # Crypto
    if s in ("BTC", "BTCUSD"):
        return "AGGTRADES"

    # Stocks / ETFs
    if s in ("TSLA", "TESLA", "AMZN", "AMAZON", "QQQ", "NASDAQ", "SLV", "SILVER", "SILVERETF"):
        return "TRADES"

    if len(s) == 3 and s.isalpha():
        return "MIDPOINT"

    if len(s) == 6 and s.isalpha():
        return "MIDPOINT"

    return "TRADES"


# =============================
# 3) FETCH M1 DATA FROM IB
# =============================
def fetch_ib_m1(
    symbol,
    host="127.0.0.1",
    port=7497,
    client_id=1500,
    lookback="6 D",
    bars=7500
):
    """
    Descarga barras M1 desde IB y devuelve DataFrame compatible con tu pipeline.
    El símbolo se recibe desde market_pipeline.py.
    """

    print(f"⏳ Descargando datos M1 desde IB para {symbol}...")

    try:
        ib = ib_connect(host=host, port=port, client_id=client_id)

        contract = _resolve_contract(symbol)
        what_to_show = _resolve_what_to_show(symbol)

        qualified = ib.qualifyContracts(contract)
        if not qualified:
            raise RuntimeError(
                f"❌ No se pudo calificar el contrato IB para {symbol}: {contract}"
            )

        contract = qualified[0]

        data = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=lookback,
            barSizeSetting="1 min",
            whatToShow=what_to_show,
            useRTH=False,
            formatDate=1,
            keepUpToDate=False
        )

        if data is None or len(data) == 0:
            raise RuntimeError(
                f"❌ No hay datos M1 en IB para {symbol} "
                f"(contract={contract}, whatToShow={what_to_show})"
            )

        df = util.df(data)

        if df.empty:
            raise RuntimeError(f"❌ IB devolvió DataFrame vacío para {symbol}")

        # ==========================================================
        # NORMALIZACIÓN COMPATIBLE CON TU PIPELINE
        # ==========================================================
        if "date" in df.columns:
            df.rename(columns={"date": "time"}, inplace=True)

        df["time"] = pd.to_datetime(df["time"])

        if "volume" not in df.columns:
            df["volume"] = 0.0

        if "spread" not in df.columns:
            df["spread"] = 0.0

        # Asegurar columnas numéricas
        for col in ["open", "high", "low", "close", "volume", "spread"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = 0.0

        # Limpiar nulos importantes
        df = df.dropna(subset=["time", "open", "high", "low", "close"]).copy()

        df["timestamp"] = df["time"].astype("int64") // 10**6
        df["color"] = [
            "green" if c >= o else "red"
            for c, o in zip(df["close"], df["open"])
        ]

        keep_cols = [
            "time", "open", "high", "low", "close",
            "volume", "spread", "timestamp", "color"
        ]

        df = df[keep_cols].tail(bars).reset_index(drop=True)

        print(f"📊 {len(df)} velas M1 cargadas correctamente desde IB para {symbol}")
        print(f"✅ Contrato usado: {contract}")
        print(f"✅ whatToShow: {what_to_show}")

        return df

    finally:
        try:
            ib_disconnect()
        except Exception:
            pass