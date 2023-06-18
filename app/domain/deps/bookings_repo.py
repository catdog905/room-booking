from abc import ABC

from app.domain.entities import Booking, TimePeriod, Room, User


class BookingsRepo(ABC):
    async def create_booking(self, booking: Booking) -> int:
        raise NotImplementedError

    async def delete_booking(self, booking_id: int):
        raise NotImplementedError

    async def get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email_address: str | None = None,
    ) -> list[Booking]:
        raise NotImplementedError

    async def get_booking_owner(self, booking_id: int) -> User:
        raise NotImplementedError
