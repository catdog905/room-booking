import exchangelib

from dataclasses import dataclass
from app.domain.entities import Booking, TimePeriod, Room, User


@dataclass
class Credentials:
    primary_smtp_address: str
    username: str
    password: str


class Adapter:
    def __init__(self, credentials: Credentials) -> None:
        self.account = exchangelib.Account(
            primary_smtp_address=credentials.primary_smtp_address,
            credentials=exchangelib.Credentials(
                username=credentials.username, password=credentials.password
            ),
        )

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
