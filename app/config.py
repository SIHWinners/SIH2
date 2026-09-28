from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    APP_NAME: str = "Digital Twin for Well-to-Surface Optimization"
    DATABASE_URL: str = "sqlite:///./digital_twin.db"
    MODEL_DIR: str = str(BASE_DIR / "models")
    TRAIN_DATA_PATH: str = str(BASE_DIR / "data" / "mock_sensor_data.csv")
    ANOMALY_MODEL_PATH: str = str(BASE_DIR / "models" / "isolation_forest.joblib")
    REGRESSOR_MODEL_PATH: str = str(BASE_DIR / "models" / "random_forest_regressor.joblib")
    SHAP_BACKGROUND_PATH: str = str(BASE_DIR / "models" / "shap_background.joblib")
    API_BASE_URL: str = "http://127.0.0.1:8000"
    SIMULATOR_INTERVAL_SECONDS: float = 3.0
    FIELD_NAME: str = "Oil India Limited - Baghewala Asset"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


settings = Settings()
