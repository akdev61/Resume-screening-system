from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )
    database_url: str = "postgresql://postgres:postgres@localhost:5432/resume_screening"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    upload_dir: str = str(PROJECT_ROOT / "uploads")
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"


settings = Settings()
