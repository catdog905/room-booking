import exchangelib

from app.domain.entities import Booking, TimePeriod, Room, User
from app.domain.dependencies import BookingsRepo
from app.domain.entities.booking import BookingWithId


class Outlook(BookingsRepo):
    def __init__(self, account: exchangelib.Account) -> None:
        self._account = account

    async def create_booking(self, booking: Booking) -> int:
        item = exchangelib.CalendarItem(
            account=self._account,
            folder=self._account.calendar,
            start=booking.period.start.datetime,
            end=booking.period.end.datetime,
            subject=booking.title,
            required_attendees=[booking.owner.email],
        )

        item.save(send_meeting_invitations=exchangelib.items.SEND_ONLY_TO_ALL)

        if item.id is None:
            # TODO(metafates): make error make informational
            raise Exception("id is none")

        return item.id

    async def _get_booking(self, booking_id: int) -> exchangelib.CalendarItem:
        # FIXME(metafates): Pyright complains about this
        # `Cannot access member "get" for type "threaded_cached_property"`
        # Though, it should be working...
        return self._account.calendar.get(id=booking_id)

    async def delete_booking(self, booking_id: int):
        booking = await self._get_booking(booking_id)
        booking.delete()

    async def get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        raise NotImplementedError

    async def get_booking_owner(self, booking_id: int) -> User:
        booking = await self._get_booking(booking_id)

        # TODO(metafates): find a way to extract attendees from booking
        # because whatever required_attendees returns makes no sense
        attendees = booking.required_attendees

        raise NotImplementedError
