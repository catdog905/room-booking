__all__ = ["Room", "Booking"]

from .common import TimePeriod
from .iam import User


# Room
class Room:
    def __init__(self, name: str, email_address: str):
        pass


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
