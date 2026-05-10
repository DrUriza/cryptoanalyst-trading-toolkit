# =====================================================
# Tech/Analyzers/topology.py
# =====================================================
import persim
import pandas as pd
import numpy  as np
from ripser   import Rips
from scipy    import sparse

def Wasserstein_Distances(data, w=20, high_on=95, high_off=80, low_on=20, low_off=35):
    idx      = data.index
    WD_full  = pd.Series(np.nan, index=idx)
    POS_full = pd.Series(0.0,   index=idx)
    close = data["close"].values
    if len(close) < 2 * w + 2:
        return WD_full.fillna(0.0), POS_full

    R_close = np.log(close[1:] / close[:-1])
    x = R_close
    N = len(x)
    I = np.arange(N - 1)
    J = np.arange(1, N)
    V = np.maximum(x[:-1], x[1:])
    I = np.concatenate([I, np.arange(N)])
    J = np.concatenate([J, np.arange(N)])
    V = np.concatenate([V, x])
    D = sparse.coo_matrix((V, (I, J)), shape=(N, N)).tocsr()

    rips    = Rips(maxdim=2, verbose=False)
    wd_vals = []
    wd_idx  = []
    for i in range(0, N - 2 * w):
        try:
            dgm1 = rips.fit_transform(D[i : i + w])
            dgm2 = rips.fit_transform(D[i + w : i + 2 * w])
            wd   = persim.wasserstein(dgm1[0], dgm2[0], matching=False)
            wd_vals.append(wd)
            wd_idx.append(idx[i + 2 * w])
        except Exception:
            continue

    if not wd_vals:
        return WD_full.fillna(0.0), POS_full

    wd_vals = np.array(wd_vals)
    wd_norm = 100 * (wd_vals - wd_vals.min()) / (wd_vals.max() - wd_vals.min() + 1e-6)
    WD_full.loc[wd_idx] = wd_norm
    WD_full = WD_full.ffill()

    POS_full[WD_full >= high_on] = 1.0
    POS_full[WD_full <= low_on]  = -1.0
    POS_full[(WD_full < high_off) & (WD_full > low_off)] = 0.0

    return WD_full.fillna(0.0), POS_full
