from app.domain.entities.time.time_stamp import TimeStamp
from app.domain.entities.exceptions.end_time_before_start_time_exception import EndTimeBeforeStartTimeException


class TimePeriod:
    def __init__(self, start: TimeStamp, end: TimeStamp):
        if end < start:
            raise EndTimeBeforeStartTimeException(start_time=start, end_time=end)
        self._start = start
        self._end = end

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end
