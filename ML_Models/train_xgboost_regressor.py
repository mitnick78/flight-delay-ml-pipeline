import json
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data_loader import get_train_test_split
from preprocessing import get_preprocessor
from config import RANDOM_STATE, DELAY_DECISION_THRESHOLD_MINUTES

def build_model():
    """
    Builds a scikit-learn Pipeline with preprocessing and XGBoost Regressor.
    """
    preprocessor = get_preprocessor()
    regressor = XGBRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        eval_metric='rmse'
    )
    
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', regressor)
    ])
    
    return model

def train_and_evaluate():
    """
    Trains the production XGBoost regressor and saves the artifact used by the API.
    """
    print("Loading data for regression...")
    X_train, X_test, y_train, y_test = get_train_test_split()
    
    model = build_model()
    
    print("Training XGBoost Regressor...")
    model.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)
    
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²:   {r2:.4f}")
    
    output_dir = Path(__file__).resolve().parent.parent / "saved_models"
    output_dir.mkdir(exist_ok=True)

    model_path = output_dir / "best_delay_regressor.joblib"
    metadata_path = output_dir / "best_delay_regressor_metadata.json"

    joblib.dump(model, model_path)

    metadata = {
        "model_name": "XGBoost Regressor",
        "target_column": "arr_delay",
        "decision_threshold_minutes": DELAY_DECISION_THRESHOLD_MINUTES,
        "prediction_rule": "Return NO DELAY when predicted delay is strictly below 0 minutes.",
        "metrics": {
            "Model": "XGBoost Regressor",
            "MAE": mae,
            "RMSE": rmse,
            "R-Squared": r2,
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Model saved to {model_path}")
    print(f"Metadata saved to {metadata_path}")
    
    return model

if __name__ == "__main__":
    train_and_evaluate()
