__all__ = ["Room", "TimeStamp", "TimePeriod", "Booking", "BookingWithId", "BookingId"]

from datetime import UTC, datetime
from enum import StrEnum
from typing import TypedDict, Unpack, assert_never

from .common import Language
from .iam import User

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


class TimeStamp:
    def __init__(self, datetime_utc: datetime):
        if datetime_utc.tzinfo not in (None, UTC):
            raise Exception("datetime_utc timezone must be UTC")
        self._datetime_utc = datetime_utc.replace(tzinfo=UTC)

    @property
    def datetime(self):
        return self._datetime_utc

    def __lt__(self, other: "TimeStamp"):
        return self._datetime_utc < other._datetime_utc

    def __le__(self, other: "TimeStamp"):
        return self._datetime_utc <= other._datetime_utc

    def __gt__(self, other: "TimeStamp"):
        return self._datetime_utc > other._datetime_utc

    def __ge__(self, other: "TimeStamp"):
        return self._datetime_utc >= other._datetime_utc


class TimePeriod:
    def __init__(self, start: TimeStamp, end: TimeStamp):
        if end < start:
            raise Exception("end must not be before start")
        self._start = start
        self._end = end

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end


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

    @property
    def id(self):
        return self._id
