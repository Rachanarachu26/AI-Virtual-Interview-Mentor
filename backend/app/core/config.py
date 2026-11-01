"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object. Values are read from the environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Database ----
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/ai_interview"

    # ---- Auth ----
    JWT_SECRET_KEY: str = "change_this_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ---- Gemini ----
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ---- Whisper ----
    WHISPER_MODEL: str = "base"

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---- Uploads ----
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10

    # ---- Evaluation weights ----
    WEIGHT_ANSWER_QUALITY: float = 0.40
    WEIGHT_COMMUNICATION: float = 0.25
    WEIGHT_EYE_CONTACT: float = 0.15
    WEIGHT_POSTURE: float = 0.10
    WEIGHT_GESTURE: float = 0.10

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def evaluation_weights(self) -> dict:
        return {
            "answer_quality": self.WEIGHT_ANSWER_QUALITY,
            "communication": self.WEIGHT_COMMUNICATION,
            "eye_contact": self.WEIGHT_EYE_CONTACT,
            "posture": self.WEIGHT_POSTURE,
            "gesture": self.WEIGHT_GESTURE,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
