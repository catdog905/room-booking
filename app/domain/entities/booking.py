__all__ = ["Room", "Booking", "BookingWithId", "BookingId", "RoomType"]

from enum import StrEnum
from typing import TypedDict, Unpack, assert_never

from .common import Language
from .iam import User
from .time.time_period import TimePeriod

BookingId = str


class RoomType(StrEnum):
    MEETING_ROOM = "MEETING_ROOM"
    AUDITORIUM = "AUDITORIUM"


class Room:
    def __init__(
            self,
            id: str,
            capacity: int,
            email: str,
            name_en: str,
            name_ru: str,
            room_type: RoomType
    ):
        self.id = id
        self.capacity = capacity
        self._email = email
        self._name_en = name_en
        self._name_ru = name_ru
        self.room_type = room_type

    @property
    def email(self):
        return self._email

    def get_name(self, lang: Language) -> str:
        match lang:
            case Language.EN:
                return self._name_en
            case Language.RU:
                return self._name_ru
            case _:
                assert_never(lang)




class BookingDict(TypedDict):
    title: str
    period: TimePeriod
    room: Room
    owner: User


class Booking:
    def __init__(
            self,
            **kwargs: Unpack[BookingDict],
    ):
        self._title = kwargs["title"]
        self._period = kwargs["period"]
        self._room = kwargs["room"]
        self._owner = kwargs["owner"]

    @property
    def title(self):
        return self._title

    @property
    def period(self):
        return self._period

    @property
    def room(self):
        return self._room

    @property
    def owner(self):
        return self._owner


class BookingWithIdDict(BookingDict):
    id: BookingId


class BookingWithId(Booking):
    def __init__(
            self,
            **kwargs: Unpack[BookingWithIdDict],
    ):
        super().__init__(**kwargs)
        self._id = kwargs["id"]

    @staticmethod
    def from_booking_and_id(booking: Booking, id: str) -> "BookingWithId":
        return BookingWithId(id=id,
                             title=booking.title,
                             period=booking.period,
                             room=booking.room,
                             owner=booking.owner)

    @property
    def id(self):
        return self._id
