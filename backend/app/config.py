from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "AdaptiveDocAI"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./trustrag.db"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    EMBEDDING_PROVIDER: str = "fallback"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    BAAI_API_KEY: Optional[str] = None
    EMBEDDING_BATCH_SIZE: int = 32
    LLM_PROVIDER: str = "fallback"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: Optional[str] = None
    LLM_TEMPERATURE: float = 0.0
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    REDIS_URL: str | None = None
    LLM_CIRCUIT_FAILURE_THRESHOLD: int = 3
    LLM_CIRCUIT_RECOVERY_SECONDS: float = 30.0

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() in {"production", "prod"} and self.JWT_SECRET == "change-me-in-production":
            raise ValueError("JWT_SECRET must be changed before running in production")
        if self.RATE_LIMIT_REQUESTS < 1 or self.RATE_LIMIT_WINDOW_SECONDS < 1:
            raise ValueError("Rate-limit settings must be positive")
        return self


settings = Settings()
