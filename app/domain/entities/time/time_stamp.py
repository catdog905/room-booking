from datetime import datetime, UTC


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

    def __str__(self):
        return str(self._datetime_utc)
