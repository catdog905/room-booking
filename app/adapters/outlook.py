from re import M
import exchangelib

from app.domain.entities import Booking, TimePeriod, Room, User
from app.domain.dependencies import BookingsRepo
from app.domain.entities.booking import BookingId, BookingWithId


class Outlook(BookingsRepo):
    def __init__(self, account: exchangelib.Account) -> None:
        self._account = account

    async def create_booking(self, booking: Booking) -> BookingId:
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

    async def _get_calendar_item(self, id: BookingId) -> exchangelib.CalendarItem:
        return self._account.calendar.get(id=id)  # type: ignore

    async def delete_booking(self, booking_id: BookingId):
        booking = await self._get_calendar_item(booking_id)
        booking.delete()

    async def get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        raise NotImplementedError

    async def get_booking_owner(self, booking_id: BookingId) -> User:
        calendar_item = await self._get_calendar_item(booking_id)
        attendees = calendar_item.required_attendees

        if not len(attendees):  # type: ignore
            # TODO(metafates): make error more informational
            raise Exception("no required attendees found")

        # Attendees list follows the following pattern:
        #
        # 1. booking service: student.booking@innopolis.ru
        # 2. the actual user: n.surname@innopolis.university
        # 3. room email: iu.resource.lectureroom314@innopolis.ru
        #
        # Yes, the room has it's own email, I know...

        # so what we need is the second attendee here
        # but perform validation before accessing it

        if len(attendees) < 2:  # type: ignore
            # TODO(metafates): make error more informational
            raise Exception("unexpected attendees count")

        owner = attendees[1]  # type: ignore

        return User(owner.mailbox.email_address)
