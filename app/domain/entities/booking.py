__all__ = ["Room", "TimeStamp", "TimePeriod", "Booking"]

from typing import assert_never
from datetime import datetime, UTC

from .common import Language
from .iam import User


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


class TimeStamp:
    def __init__(self, datetime_utc: datetime):
        if datetime_utc.tzinfo not in (None, UTC):
            raise Exception("datetime_utc timezone must be UTC")
        self._datetime_utc = datetime_utc.replace(tzinfo=UTC)

    @property
    def datetime(self):
        return self._datetime_utc


class TimePeriod:
    def __init__(self, start: TimeStamp, end: TimeStamp):
        self._start = start
        self._end = end

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end


class Booking:
    def __init__(
        self,
        *,
        title: str,
        period: TimePeriod,
        room: Room,
        owner: User,
    ):
        self._title = title
        self._period = period
        self._room = room
        self._owner = owner

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
