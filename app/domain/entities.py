from datetime import datetime, tzinfo


class User:
    def __init__(self, email_address: str):
        pass

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        raise NotImplementedError


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
        creator: User,
    ):
        self._title = title
        self._period = period
        self._room = room
        self._creator = creator
