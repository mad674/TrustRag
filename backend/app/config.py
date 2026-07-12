from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./trustrag.db"
    QDRANT_URL: str = "local"
    JWT_SECRET: str = "changeme"
    EMBEDDING_PROVIDER: str = "fallback"  # options: openai, baai, sentence-transformers, fallback
    OPENAI_API_KEY: Optional[str] = None
    BAAI_API_KEY: Optional[str] = None
    EMBEDDING_BATCH_SIZE: int = 32

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")

settings = Settings()
