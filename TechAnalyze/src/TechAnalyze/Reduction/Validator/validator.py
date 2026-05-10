# =====================================================
# Reduction/Validator/validator.py
# =====================================================
import numpy as np
import pandas as pd
def validate_dataframe(df, name):
    if df is None or df.empty:
        print(f"[Validator] {name}: DF vacío.")
        return None, df
    pca_cols = [c for c in df.columns if c.startswith("PCA_")]
    if not pca_cols:
        print(f"[Validator] {name}: Sin PCA components.")
    else:
        print(f"[Validator] {name}: {len(pca_cols)} PCA components verificados.")
    target_cols = [c for c in ["future_return", "target_bin", "dynamic_threshold", "trend_score"] if c in df.columns]
    allowed_patterns = ["PCA_",
                        "top_spread",
                        "depth_imbalance",
                        "liq_wall_",
                        "bid_concentration",
                        "ask_concentration",
                        "_norm",
                        "vol_ratio",
                        "spread_rel",
                        "high_vol_flag",
                        ".Fza",
                        ".FzaT"]
    allowed_cols = set(target_cols)
    for col in df.columns:
        if col.startswith("PCA_"):
            allowed_cols.add(col)
        elif any(p in col for p in allowed_patterns):
            allowed_cols.add(col)
    df_filtered = df[list(allowed_cols)].copy()
    df_filtered = df_filtered.select_dtypes(include=[np.number])
    df_filtered = df_filtered.replace([np.inf, -np.inf], np.nan)
    nan_counts  = df_filtered.isna().sum().to_dict()
    df_filtered = df_filtered.dropna()
    report = {"dataset": name,
              "rows": len(df_filtered),
              "nan_counts": nan_counts,
              "inf_counts": {},  
              "targets": {}}
    for col in target_cols:
        if col in df_filtered.columns:
            if df_filtered[col].dtype.kind in "fc":
                report["targets"][col] = {"mean": float(df_filtered[col].mean()),
                                          "std":  float(df_filtered[col].std()),
                                          "low":  float(df_filtered[col].min()),
                                          "high":  float(df_filtered[col].max())}
            else:
                report["targets"][col] = (df_filtered[col].value_counts().to_dict())
    return report, df_filtered
