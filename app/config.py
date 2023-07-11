__all__ = ["Environment", "Config", "config", "bookable_rooms"]

from enum import StrEnum

from pydantic import AnyHttpUrl, BaseSettings, Field

from app.domain.entities.booking import Room
from app.domain.entities.booking import RoomType


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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
