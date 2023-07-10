from datetime import datetime, timedelta, timezone


# Moment in time
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

    def datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(self._timestamp, tz=timezone.utc)

    @staticmethod
    def now() -> "TimeStamp":
        return TimeStamp(datetime.now(tz=timezone.utc).timestamp())


# Period in time
class TimePeriod:
    def __init__(self, start: TimeStamp, end: TimeStamp):
        self._start = start
        self._end = end
