"""
Central application configuration.

RULE 10 / RULE 11 (project architecture rules):
All thresholds and model paths must be configurable, not hard-coded
inside detection/fusion logic. This module is the single source of
truth for that configuration, loaded from environment variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "Proctoring System API"
    app_version: str = "0.1.0"
    environment: str = "development"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- CORS (frontend origin during local dev) ---
    frontend_origin: str = "http://localhost:5173"

    # --- Model paths (populated in later phases; kept here now so the
    # config surface is fixed from Phase 0 onward, per RULE 11) ---
    face_model_path: str = "ml/models/face/yolov8n.pt"
    emotion_model_path: str = "ml/models/emotion/"
    fusion_model_path: str = "ml/models/fusion/"
    temporal_model_path: str = "ml/models/temporal/"

    # --- Thresholds (placeholders for Phase 1+, kept configurable per RULE 10) ---
    gaze_away_threshold: float = 0.35
    head_turn_yaw_threshold: float = 30.0
    head_turn_pitch_threshold: float = 20.0
    suspicion_flag_threshold: float = 0.5

    class Config:
        env_file = ".env"
        env_prefix = "PROCTOR_"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so config is loaded once (RULE 13)."""
    return Settings()
