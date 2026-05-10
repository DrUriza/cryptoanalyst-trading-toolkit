from ib_insync import IB
import time

_IB        = None
_CLIENT_ID = None

def ib_connect(host="127.0.0.1", port=7497, client_id=101, timeout=5) -> IB:
    global _IB, _CLIENT_ID
    # Si ya existe conexión activa, reutilizarla
    if _IB is not None and _IB.isConnected():
        return _IB
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=timeout)
        _IB = ib
        _CLIENT_ID = client_id
    except Exception:
        retry_id = client_id + 1
        print(f"⚠ IB estaba ocupada, reintentando clientId +1 → {retry_id}")
        ib = IB()
        ib.connect(host, port, clientId=retry_id, timeout=timeout)
        _IB = ib
        _CLIENT_ID = retry_id
    time.sleep(0.8)
    return _IB
def ib_disconnect(full=False):
    global _IB, _CLIENT_ID
    if full and _IB is not None and _IB.isConnected():
        _IB.disconnect()
        time.sleep(0.8)
    if full:
        _IB = None
        _CLIENT_ID = None
def ib_get_connection():
    global _IB
    return _IB
def ib_get_client_id():
    global _CLIENT_ID
    return _CLIENT_ID