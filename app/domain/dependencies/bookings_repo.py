from abc import ABC, abstractmethod

from app.domain.entities import Booking, BookingId, Room, TimePeriod, User
from app.domain.entities.booking import BookingWithId


class BookingsRepo(ABC):
    @abstractmethod
    async def create_booking(self, booking: Booking) -> BookingId:
        pass

    @abstractmethod
    async def delete_booking(self, booking_id: BookingId):
        pass

    @abstractmethod
    async def get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        pass

    @abstractmethod
    async def get_booking_owner(self, booking_id: BookingId) -> User:
        pass
