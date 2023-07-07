__all__ = ["Environment", "Config", "config"]

from enum import StrEnum

from pydantic import AnyHttpUrl, BaseSettings

from app.domain.entities import Room
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

    outlook_email: str = "vladislav@0f4tw.onmicrosoft.com"

    app_tenant_id: str = "6f87849e-85b5-4661-ab58-ba9d87d3469a"
    app_client_id: str = "c38ece28-3e8e-4dc8-88be-84b4d67cc843"
    app_secret: str = "lTn8Q~p_gAqeqwHR2pXp1NazJJttd7JJ~KI~1bfE"
    app_secret_id: str = "55eaaa43-b240-46ef-9983-65b05e1658c4"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
