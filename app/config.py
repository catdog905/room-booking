__all__ = ["Environment", "Config", "config", "bookable_rooms"]

from datetime import timedelta
from enum import StrEnum

from app.domain.entities.booking import Room
from app.domain.entities.booking import RoomType
from pydantic import AnyHttpUrl, BaseSettings, Field


bookable_rooms = [
        Room(id="313",
             capacity=5,
             email="iu.resource.lectureroom313@0f4tw.onmicrosoft.com",
             name_en="Meeting room",
             name_ru="Переговорка",
             room_type=RoomType.MEETING_ROOM)
    ]


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

    outlook_email: str = Field(default=...)
    app_tenant_id: str = Field(default=...)
    app_client_id: str = Field(default=...)
    app_secret: str = Field(default=...)
    app_secret_id: str = Field(default=...)

    secret_key: str = Field(default=...)
    access_token_lifetime: timedelta = timedelta(minutes=15)
    refresh_token_lifetime: timedelta = timedelta(days=30)

    # Map {"name": "api_key"}
    authorized_integrations: dict[str, str] = Field(default_factory=lambda: {})

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
