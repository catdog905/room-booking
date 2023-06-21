from datetime import datetime, tzinfo


class User:
    def __init__(self, email_address: str):
        self.email_address = email_address

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        raise NotImplementedError


# Room
class Room:
    def __init__(self, name: str, email_address: str):
        self.name = name
        self.email_address = email_address


# Moment in time
class TimeStamp:
    def __init__(self, dt: datetime, tz: tzinfo):
        if dt.tzinfo is not None and dt.tzinfo != tz:
            raise Exception("dt must not have a tzinfo set or it should match with tz")
        self.datetime = dt
        self.timezone = tz


# Period in time
class TimePeriod:
    def __init__(self, start: TimeStamp, end: TimeStamp):
        self.start = start
        self.end = end


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
        self.title = title
        self.period = period
        self.room = room
        self.creator = creator
