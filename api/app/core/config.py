from __future__ import annotations

from pathlib import Path

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Industrial Maintenance Platform", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_v1_prefix: str = Field(default="/api/v1", alias="BACKEND_API_V1_PREFIX")
    host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    port: int = Field(default=8000, alias="BACKEND_PORT")
    secret_key: str = Field(default="change-this-secret-key", alias="BACKEND_SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=480,
        alias="BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    allowed_origins_raw: str = Field(
        default="http://localhost:8550,http://127.0.0.1:8550",
        alias="BACKEND_ALLOWED_ORIGINS",
    )
    database_url: str = Field(
        default="sqlite+pysqlite:///./maintenance_platform.db",
        alias="DATABASE_URL",
    )
    auto_seed: bool = Field(default=True, alias="BACKEND_AUTO_SEED")
    default_admin_email: EmailStr = Field(
        default="admin@maintenance.example.com",
        alias="DEFAULT_ADMIN_EMAIL",
    )
    default_admin_password: str = Field(
        default="Admin@123",
        alias="DEFAULT_ADMIN_PASSWORD",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins_raw.split(",") if item.strip()]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
