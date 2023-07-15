from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities.booking import Room, RoomType, BookingWithId
from app.domain.entities.common import Language


class RoomSchema(BaseModel):
    name: str
    id: str
    type: RoomType
    capacity: int

    @staticmethod
    def from_room(room: Room, language: Language) -> "RoomSchema":
        return RoomSchema(id=room.id, name=room.get_name(language), type=room.room_type, capacity=room.capacity)

    class Config:
        schema_extra = {
            "example": {
                "name": "Meeting Room #3.2",
                "id": "3.2",
                "type": RoomType.MEETING_ROOM,
                "capacity": 6,
            }
        }


class BookingWithIdSchema(BaseModel):
    id: str
    title: str
    start: datetime
    end: datetime
    room: RoomSchema
    owner_email: str

    @staticmethod
    def from_booking_with_id(booking: BookingWithId, language: Language) -> "BookingWithIdSchema":
        return BookingWithIdSchema(id=booking.id,
                                   title=booking.title,
                                   start=booking.period.start.datetime_utc(),
                                   end=booking.period.end.datetime_utc(),
                                   room=RoomSchema.from_room(booking.room, language),
                                   owner_email=booking.owner.email)


class BookingsFilter(BaseModel):
    started_at_or_after: datetime = Field(
        ...,
        description="When specified, only bookings that started at this time "
                    "or later will be returned.",
    )
    ended_at_or_before: datetime = Field(
        ...,
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


class BookRoomError(BaseModel):
    message: str


class QueryBookingsRequest(BaseModel):
    filter: BookingsFilter
