from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RoomType(StrEnum):
    MEETING_ROOM = "MEETING_ROOM"
    AUDITORIUM = "AUDITORIUM"


class Room(BaseModel):
    name: str
    id: str
    type: RoomType
    capacity: int

    class Config:
        schema_extra = {
            "example": {
                "name": "Meeting Room #3.2",
                "id": "3.2",
                "type": RoomType.MEETING_ROOM,
                "capacity": 6,
            }
        }


class Booking(BaseModel):
    id: str
    title: str
    start: datetime
    end: datetime
    room: Room
    owner_email: str


class BookingsFilter(BaseModel):
    started_at_or_after: datetime | None = Field(
        None,
        description="When specified, only bookings that started at this time "
        "or later will be returned.",
    )
    ended_at_or_before: datetime | None = Field(
        None,
        description="When specified, only bookings that ended at this time "
        "or sooner will be returned.",
    )
    room_id_in: list[str] | None = Field(
        None,
        description="When specified, only bookings of the rooms from the "
        "list will be returned.",
    )
    owner_email_in: list[str] | None = Field(
        None,
        description="When specified, only bookings with the owner with "
        "email address from the list will be returned.",
    )


class GetFreeRoomsRequest(BaseModel):
    start: datetime
    end: datetime


class BookRoomRequest(BaseModel):
    title: str
    start: datetime
    end: datetime
    owner_email: str | None = Field(
        None,
        description="Owner email address of the booking. Can be omitted, if "
        "the request is made by the user who books a room.",
    )


class BookRoomError(BaseModel):
    message: str


class QueryBookingsRequest(BaseModel):
    filter: BookingsFilter
