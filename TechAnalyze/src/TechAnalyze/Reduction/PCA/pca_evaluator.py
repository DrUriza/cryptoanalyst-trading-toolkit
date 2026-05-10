# =====================================================
# Reduction/PCA/pca_evaluator.py
# =====================================================
import numpy                 as np
from sklearn.decomposition   import PCA
from sklearn.preprocessing   import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model    import LinearRegression
from sklearn.metrics         import mean_squared_error

all_results   = {}
best          = {}
# -----------------------------------------------------------
#     🌌 Selección de componentes óptimos
# -----------------------------------------------------------
def choose_optimal_components(pca):
        explained = np.cumsum(pca.explained_variance_ratio_)
        k = np.argmax(explained >= 0.95) + 1
        return k
# -----------------------------------------------------------
#     🧠 Ejecución completa de PCA
# -----------------------------------------------------------
def run_pca(df, interval):
        try:
            df = df.copy()
            # -----------------------------
            # 1. Separar targets
            # -----------------------------
            target_cols = [c for c in ["future_return", "target_bin", "trend_score"] if c in df.columns]
            X = df.drop(columns=target_cols, errors="ignore")
            # -----------------------------
            # 2. Limpiar columnas no numéricas
            # -----------------------------
            numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
            X = X[numeric_cols]
            if X.empty:
                print(f"[PCA][WARN] {interval}: No hay columnas numéricas para PCA.")
                return df
            # -----------------------------
            # 3. Remover NaN / inf
            # -----------------------------
            X = X.replace([np.inf, -np.inf], np.nan).dropna(axis=0)
            if X.empty:
                print(f"[PCA][WARN] {interval}: Todo se volvió NaN/inf.")
                return df
            # -----------------------------
            # 4. Escalado
            # -----------------------------
            scaler   = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            # -----------------------------
            # 5. PCA preliminar
            # -----------------------------
            pca_full = PCA()
            pca_full.fit(X_scaled)
            k = choose_optimal_components(pca_full)
            # -----------------------------
            # 6. PCA final
            # -----------------------------
            pca = PCA(n_components=k)
            principal_components = pca.fit_transform(X_scaled)
            # -----------------------------
            # 7. Insertar PCA_n al DF
            # -----------------------------
            df = df.loc[X.index].reset_index(drop=True)
            # Insertar PCA components
            for i in range(k):
                df[f"PCA_{i+1}"] = principal_components[:, i]
            # -----------------------------
            # 8. Evaluación opcional (tu regresión)
            # -----------------------------
            if "future_return" in target_cols:
                try:
                    X_train, X_test, y_train, y_test = train_test_split(principal_components, df.loc[X.index, "future_return"], test_size=0.2, shuffle=False)
                    model = LinearRegression()
                    model.fit(X_train, y_train)
                    preds = model.predict(X_test)
                    rmse  = np.sqrt(mean_squared_error(y_test, preds))
                except Exception:
                    rmse = None
            else:
                rmse = None
            # -----------------------------
            # 9. Guardar resultados
            # -----------------------------
            all_results[interval] = {"n_components": k, "variance_ratio": pca.explained_variance_ratio_.tolist(), "rmse": rmse}
            print(f"[PCA] {interval}: OK con {k} componentes. RMSE={rmse}")
            return df
        except Exception as e:
            print(f"[PCA][ERROR] {e}")
            return df

