"""
Application configuration using Pydantic Settings.
Loads from .env file and environment variables.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_SECRET = "career-platform-secret-key-change-in-production"


class Settings(BaseSettings):
    APP_NAME: str = "Career Automation & Job Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    SECRET_KEY: str = _DEFAULT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'career_platform.db'}"
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    DEFAULT_MODEL_PROVIDER: str = "gemini"
    AI_MODE: str = "auto"

    ENABLE_COST_TRACKING: bool = True
    MAX_MONTHLY_COST_USD: float = 50.0

    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    GENERATED_DIR: str = str(BASE_DIR / "data" / "generated")
    TEMPLATE_DIR: str = str(BASE_DIR / "templates")

    GITHUB_TOKEN: Optional[str] = None

    # FIX: typed as List[str] so CORS_ORIGINS works correctly with middleware
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# FIX: Raise loud error if default secret key used in production
if not settings.DEBUG and settings.SECRET_KEY == _DEFAULT_SECRET:
    raise RuntimeError(
        "SECURITY ERROR: SECRET_KEY is still the default value. "
        "Set a strong random SECRET_KEY in your .env before running in production."
    )

for dir_path in [settings.UPLOAD_DIR, settings.GENERATED_DIR, settings.CHROMA_PERSIST_DIR]:
    os.makedirs(dir_path, exist_ok=True)
