from datetime import datetime, UTC, timedelta, timezone


class TimeStamp:
    def __init__(self, timestamp: float):
        """
        :param timestamp: POSIX timestamp (number of seconds from epoch).
        """
        self._timestamp = timestamp

    def __add__(self, other):
        if not isinstance(other, timedelta):
            raise TypeError(
                "unsupported operand type(s) for +: 'TimeStamp' and '{}'".format(
                    type(other)
                )
            )
        return TimeStamp(self._timestamp + other.total_seconds())

    def __le__(self, other):
        if not isinstance(other, TimeStamp):
            raise TypeError(
                "unsupported operand type(s) for <=: 'TimeStamp' and '{}'".format(
                    type(other)
                )
            )
        return self._timestamp <= other._timestamp

    def __ge__(self, other):
        if not isinstance(other, TimeStamp):
            raise TypeError(
                "unsupported operand type(s) for >=: 'TimeStamp' and '{}'".format(
                    type(other)
                )
            )
        return self._timestamp >= other._timestamp

    def __lt__(self, other):
        if not isinstance(other, TimeStamp):
            raise TypeError(
                "unsupported operand type(s) for <: 'TimeStamp' and '{}'".format(
                    type(other)
                )
            )
        return self._timestamp < other._timestamp

    def __gt__(self, other):
        if not isinstance(other, TimeStamp):
            raise TypeError(
                "unsupported operand type(s) for >: 'TimeStamp' and '{}'".format(
                    type(other)
                )
            )
        return self._timestamp > other._timestamp

    def __str__(self):
        return str(self.datetime_utc())

    def datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(self._timestamp, tz=timezone.utc)

    @staticmethod
    def now() -> "TimeStamp":
        return TimeStamp(datetime.now(tz=timezone.utc).timestamp())


class TimeStampFromDateTime(TimeStamp):
    def __init__(self, datetime: datetime):
        super().__init__(datetime.timestamp())


class CurrentTimeStamp(TimeStampFromDateTime):
    def __init__(self):
        super().__init__(datetime.now())


class ShiftedForwardTimeStamp(TimeStampFromDateTime):
    def __init__(self, timestamp: TimeStamp, shift: timedelta):
        super().__init__(timestamp.datetime_utc() + shift)


class ShiftedBackwardTimeStamp(TimeStampFromDateTime):
    def __init__(self, timestamp: TimeStamp, shift: timedelta):
        super().__init__(timestamp.datetime_utc() - shift)
