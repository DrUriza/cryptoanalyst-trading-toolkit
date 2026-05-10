from sklearn.ensemble     import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm          import SVC
from sklearn.linear_model import LogisticRegression
from xgboost              import XGBClassifier  

class ModelRegistry:
    """
    Diccionario de clasificadores disponibles.
    """
    MODELS = {"RandomForest":       RandomForestClassifier,
              "GradientBoosting":   GradientBoostingClassifier,
              "SVM":                SVC,
              "LogisticRegression": LogisticRegression,
              "XGBoost":            XGBClassifier,}
    @classmethod
    def get(cls, name):
        """Devuelve la clase del modelo por nombre."""
        return cls.MODELS.get(name)
    @classmethod
    def list(cls):
        """Lista los modelos disponibles."""
        return list(cls.MODELS.keys())
