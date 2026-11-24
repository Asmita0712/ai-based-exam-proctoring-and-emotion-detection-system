"""
Central application configuration.

RULE 10 / RULE 11 (project architecture rules):
All thresholds, model paths, and connection settings must be configurable,
loaded from environment variables with safe defaults.
"""
from functools import lru_cache
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "SentinelProctor AI API"
    app_version: str = "2.0.0"
    environment: str = os.getenv("PROCTOR_ENV", os.getenv("ENVIRONMENT", "development"))

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", os.getenv("PROCTOR_PORT", "8000")))

    # --- CORS (frontend origins) ---
    frontend_origin: str = os.getenv("PROCTOR_FRONTEND_ORIGIN", os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"))
    additional_origins: str = os.getenv("PROCTOR_ADDITIONAL_ORIGINS", "")

    # --- Database & Persistence ---
    # Automatically read DATABASE_URL (standard on Render/Neon) or PROCTOR_DATABASE_URL
    database_url: str = os.getenv("DATABASE_URL") or os.getenv("PROCTOR_DATABASE_URL") or "sqlite:///./sentinelproctor.db"

    # --- Security & JWT Authentication ---
    jwt_secret: str = os.getenv("PROCTOR_JWT_SECRET", "sentinel_proctor_secret_key_change_in_production_38942")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    attempt_token_expire_minutes: int = 360  # 6 hours

    # --- Free-Tier Resource Control ---
    # Render Free tier provides 512MB RAM. Heavy PyTorch/YOLO models are disabled
    # by default to prevent OOM SIGKILL, while browser tracking & rule scoring remain 100% active.
    enable_heavy_ai: bool = os.getenv("PROCTOR_ENABLE_HEAVY_AI", os.getenv("ENABLE_HEAVY_AI", "false")).lower() in ("true", "1", "yes")

    # --- Default Initial Provisioning Credentials ---
    admin_email: str = os.getenv("PROCTOR_ADMIN_EMAIL", "admin@sentinelproctor.ai")
    admin_password: str = os.getenv("PROCTOR_ADMIN_PASSWORD", "Admin@Sentinel2026")
    teacher_email: str = os.getenv("PROCTOR_TEACHER_EMAIL", "teacher@sentinelproctor.ai")
    teacher_password: str = os.getenv("PROCTOR_TEACHER_PASSWORD", "Teacher@Sentinel2026")

    # --- AI Models ---
    face_model_path: str = "ml/models/face/yolov8n.pt"
    emotion_model_path: str = "ml/models/emotion/"
    fusion_model_path: str = "ml/models/fusion/"
    temporal_model_path: str = "ml/models/temporal/"

    # --- Calibrated Proctoring Thresholds ---
    gaze_away_threshold: float = 0.35
    head_turn_yaw_threshold: float = 20.0
    head_turn_pitch_up_threshold: float = 16.0
    head_turn_pitch_down_threshold: float = 23.0
    suspicion_flag_threshold: float = 0.50

    # --- Scalability & Adaptive Backpressure ---
    max_queue_depth: int = 1500
    adaptive_sampling: bool = True
    target_frame_interval_ms: int = 1000

    class Config:
        env_file = ".env"
        env_prefix = "PROCTOR_"
        extra = "allow"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so config is loaded once (RULE 13)."""
    return Settings()
