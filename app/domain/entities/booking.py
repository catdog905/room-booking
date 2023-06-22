__all__ = ["Room", "TimeStamp", "TimePeriod", "Booking"]

from datetime import datetime, tzinfo

from .iam import User


# Room
class Room:
    def __init__(self, name: str, email_address: str):
        pass


# Moment in time
class TimeStamp:
    def __init__(self, dt: datetime, tz: tzinfo):
        if dt.tzinfo is not None and dt.tzinfo != tz:
            raise Exception("dt must not have a tzinfo set or it should match with tz")
        self._datetime = dt
        self._timezone = tz


# Period in time
class TimePeriod:
    def __init__(self, start: TimeStamp, end: TimeStamp):
        self._start = start
        self._end = end


# Single booking
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
