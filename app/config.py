__all__ = ["Environment", "Config", "config"]

from enum import StrEnum

from pydantic import BaseSettings, AnyHttpUrl


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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
