# =====================================================
# Tech/Analyzers/regression.py
# =====================================================
import numpy                as np
from sklearn.linear_model   import LinearRegression
from sklearn.preprocessing  import PolynomialFeatures
from sklearn.metrics        import mean_squared_error


def Regressor(data):
        df_Close = data['close'].dropna(axis='rows')
        P_Close  = df_Close.to_numpy()
        # Polynomial fitting
        min_error = float('inf')
        time = np.arange(1, len(P_Close) + 1).reshape(-1, 1)
        for degree in range(1, 16):
            poly_reg = PolynomialFeatures(degree=degree)
            x_poly = poly_reg.fit_transform(time)
            model = LinearRegression().fit(x_poly, P_Close)
            y_pred = model.predict(x_poly)
            error = mean_squared_error(P_Close, y_pred)
            if error < min_error:
                min_error      = error
                optimal_degree = degree
                optimal_y_pred = y_pred
        # Prediccion optima de los valores
        return optimal_y_pred, optimal_degree