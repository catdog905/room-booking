__all__ = ["Room", "Booking", "BookingWithId", "BookingId"]


from datetime import UTC, datetime
from typing import TypedDict, Unpack, assert_never

from .common import Language, TimePeriod
from .iam import User

BookingId = str


class Room:
    def __init__(
        self,
        email: str,
        name_en: str,
        name_ru: str,
    ):
        self._email = email
        self._name_en = name_en
        self._name_ru = name_ru

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

    @property
    def id(self):
        return self._id
