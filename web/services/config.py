from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReflexFrontendSettings(BaseSettings):
    app_name: str = Field(default="Industrial Maintenance Platform", alias="APP_NAME")
    api_base_url: str = Field(default="http://127.0.0.1:8000/api/v1", alias="REFLEX_API_BASE_URL")
    request_timeout_seconds: float = Field(default=15.0, alias="REFLEX_API_TIMEOUT")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = ReflexFrontendSettings()
