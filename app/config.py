__all__ = ["Environment", "Config", "config"]

from datetime import timedelta
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseSettings, Field


class Environment(StrEnum):
    DEVELOPMENT = "DEV"
    PRODUCTION = "PROD"
    TESTING = "TEST"


class Config(BaseSettings):
    app_title: str = "Room Booking Service"
    app_version: str = "0.1.0"
    app_description: str = "Innopolis University room booking service API."

    environment: Environment = Environment.PRODUCTION

    cors_allowed_origins: list[AnyHttpUrl] = []

    secret_key: str = Field(default=...)
    access_token_lifetime: timedelta = timedelta(minutes=15)
    refresh_token_lifetime: timedelta = timedelta(days=30)

    # Map {"name": "api_key"}
    authorized_integrations: dict[str, str] = Field(default_factory=lambda: {})

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
