from app.domain.entities.time.time_stamp import TimeStamp


class EndTimeBeforeStartTimeException(Exception):
    def __init__(self, start_time: TimeStamp, end_time: TimeStamp):
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return f"EndTimeBeforeStartTimeException: start_time = {self.start_time}, end_time = {self.end_time}"
