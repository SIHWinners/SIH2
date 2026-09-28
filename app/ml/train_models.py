from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.ml.mock_data import generate_mock_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANOMALY_FEATURE_COLS = [
    "casing_pressure", "tubing_pressure", "polished_rod_load", "stroke_speed", "motor_temp",
    "casing_pressure_lag1", "tubing_pressure_lag1", "polished_rod_load_lag1", "stroke_speed_lag1", "motor_temp_lag1",
    "casing_pressure_rolling_mean_3", "tubing_pressure_rolling_mean_3", "polished_rod_load_rolling_mean_3",
    "stroke_speed_rolling_mean_3", "motor_temp_rolling_mean_3",
]

REGRESSION_FEATURE_COLS = [
    "casing_pressure", "tubing_pressure", "polished_rod_load", "motor_temp",
    "casing_pressure_lag1", "tubing_pressure_lag1", "polished_rod_load_lag1", "motor_temp_lag1",
    "casing_pressure_rolling_mean_3", "tubing_pressure_rolling_mean_3", "polished_rod_load_rolling_mean_3",
    "motor_temp_rolling_mean_3",
]


def build_training_data(dataset_path: str | Path) -> pd.DataFrame:
    """Load and engineer lag and rolling window features for time-series modeling."""
    logger.info("Loading dataset from %s", dataset_path)
    df = pd.read_csv(dataset_path, parse_dates=["timestamp"])
    df = df.sort_values(["well_id", "timestamp"]).reset_index(drop=True)

    numeric_cols = ["casing_pressure", "tubing_pressure", "polished_rod_load", "stroke_speed", "motor_temp"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Groupby well_id to create proper time-series lag and rolling statistics
    for col in numeric_cols:
        df[f"{col}_lag1"] = df.groupby("well_id")[col].shift(1)
        df[f"{col}_rolling_mean_3"] = df.groupby("well_id")[col].transform(
            lambda s: s.rolling(3, min_periods=1).mean()
        )

    clean_df = df.dropna(subset=[f"{col}_lag1" for col in numeric_cols]).reset_index(drop=True)
    logger.info("Engineered feature set ready: %d rows", len(clean_df))
    return clean_df


def train_anomaly_model(train_df: pd.DataFrame) -> tuple[Pipeline, dict[str, float]]:
    """Train an IsolationForest model for well failure and anomaly detection."""
    logger.info("Training IsolationForest anomaly detection pipeline...")
    X = train_df[ANOMALY_FEATURE_COLS]

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("isolation_forest", IsolationForest(
                contamination=0.035,
                random_state=42,
                n_estimators=150,
                n_jobs=-1,
            )),
        ]
    )
    pipeline.fit(X)

    preds = pipeline.predict(X)
    anomaly_fraction = float(np.mean(preds == -1))
    metrics = {"anomaly_fraction": round(anomaly_fraction, 4), "n_samples": len(X)}
    logger.info("IsolationForest trained. Detected anomaly rate: %.2f%%", anomaly_fraction * 100)
    return pipeline, metrics


def train_regression_model(train_df: pd.DataFrame) -> tuple[Pipeline, dict[str, float]]:
    """Train a RandomForestRegressor to predict optimal strokes per minute (SPM)."""
    logger.info("Training RandomForest optimal speed regressor...")
    # Train only on active pumping operations (stroke_speed > 3.0 SPM)
    active_mask = train_df["stroke_speed"] >= 3.0
    active_df = train_df[active_mask]

    X = active_df[REGRESSION_FEATURE_COLS]
    y = active_df["stroke_speed"]

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("regressor", RandomForestRegressor(
                n_estimators=150,
                random_state=42,
                max_depth=12,
                min_samples_leaf=3,
                n_jobs=-1,
            )),
        ]
    )
    pipeline.fit(X, y)

    y_pred = pipeline.predict(X)
    r2 = float(r2_score(y, y_pred))
    mae = float(mean_absolute_error(y, y_pred))
    metrics = {"r2_score": round(r2, 4), "mae_spm": round(mae, 4), "n_samples": len(X)}
    logger.info("Regressor trained. R²: %.4f, MAE: %.4f SPM", r2, mae)
    return pipeline, metrics


def create_shap_background(train_df: pd.DataFrame) -> np.ndarray:
    """Extract representative background samples for low-latency SHAP explainability."""
    X = train_df[ANOMALY_FEATURE_COLS].dropna()
    # Sample 100 representative rows
    if len(X) > 100:
        sample_indices = np.linspace(0, len(X) - 1, 100, dtype=int)
        background = X.iloc[sample_indices].to_numpy()
    else:
        background = X.to_numpy()
    return background


def save_model_metadata(
    dataset_path: str | Path,
    anomaly_metrics: dict[str, float],
    regressor_metrics: dict[str, float],
) -> None:
    """Persist engineering metadata and feature registries."""
    model_dir = Path(settings.MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "dataset_path": str(Path(dataset_path)),
        "anomaly_feature_columns": ANOMALY_FEATURE_COLS,
        "regression_feature_columns": REGRESSION_FEATURE_COLS,
        "anomaly_metrics": anomaly_metrics,
        "regressor_metrics": regressor_metrics,
        "problem_statement": "SIH26120 - Oil India Digital Twin (CSS & SRP)",
        "version": "2.0.0",
    }
    with open(model_dir / "model_metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


def train_models() -> dict[str, object]:
    """Execute complete end-to-end dataset creation, training, and artifact persistence."""
    dataset_path = Path(settings.TRAIN_DATA_PATH)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)

    if not dataset_path.exists():
        logger.info("Generating realistic synthetic dataset...")
        generate_mock_dataset(dataset_path, days=120)

    df = build_training_data(dataset_path)
    anomaly_model, anomaly_metrics = train_anomaly_model(df)
    regressor_model, regressor_metrics = train_regression_model(df)
    shap_background = create_shap_background(df)

    model_dir = Path(settings.MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(anomaly_model, settings.ANOMALY_MODEL_PATH)
    joblib.dump(regressor_model, settings.REGRESSOR_MODEL_PATH)
    joblib.dump(shap_background, settings.SHAP_BACKGROUND_PATH)
    save_model_metadata(dataset_path, anomaly_metrics, regressor_metrics)

    logger.info("Models and SHAP background successfully saved.")
    return {
        "dataset_path": str(dataset_path),
        "anomaly_model_path": settings.ANOMALY_MODEL_PATH,
        "regressor_model_path": settings.REGRESSOR_MODEL_PATH,
        "shap_background_path": settings.SHAP_BACKGROUND_PATH,
        "anomaly_metrics": anomaly_metrics,
        "regressor_metrics": regressor_metrics,
    }


if __name__ == "__main__":
    result = train_models()
    print(json.dumps(result, indent=2))
