
from app.domain.entities.time.time_stamp import TimeStamp
from app.domain.entities.exceptions.end_time_before_start_time_exception import EndTimeBeforeStartTimeException


# Period in time
class TimePeriod:
    def __init__(self, start: TimeStamp, end: TimeStamp):
        if end < start:
            raise EndTimeBeforeStartTimeException(start_time=start, end_time=end)
        self._start = start
        self._end = end

    @property
    def start(self) -> TimeStamp:
        return self._start

    @property
    def end(self) -> TimeStamp:
        return self._end

    def __str__(self):
        return f'start={str(self.start)}; end={str(self.end)} '
