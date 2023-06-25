from datetime import datetime
import exchangelib
import collections.abc

from app.domain.entities import Booking, TimePeriod, Room, User
from app.domain.dependencies import BookingsRepo
from app.domain.entities.booking import BookingId, BookingWithId, TimeStamp


def calendar_item_owner(item: exchangelib.CalendarItem) -> User:
    # We have to deal with two* cases here
    #
    # 1. Some meetings has owner (the actual user that booked the room)
    #    in the `required_attendes` field
    #   a. Usually as the second one, the first one is the booking system itself
    #   b. But very rarely the owner can be the first one, so we check
    #      so we check condition (a) and if it fails try (b)
    # 2. Other meetings (usually old ones) has owner in the `organizer`
    #    field. So if (1) fails, try this

    email_address: str

    if (attendees := item.required_attendees) is not None:
        assert isinstance(attendees, collections.abc.Sequence)

        attendee: exchangelib.Attendee
        if len(attendees) > 1:
            attendee = attendees[1]
        elif len(attendees) == 1:
            attendee = attendees[0]
        else:
            # TODO(metafates): improve these error messages
            raise Exception("no attendees")

        mailbox = attendee.mailbox
        assert mailbox is not None and isinstance(mailbox, exchangelib.Mailbox)

        email_address = str(mailbox.email_address)
    elif (organizer := item.organizer) is not None:
        assert isinstance(organizer, exchangelib.Mailbox)

        email_address = str(organizer.email_address)
    else:
        # TODO(metafates): improve these error messages
        raise Exception("failed to get calendar item owner")

    return User(email_address)


def calendar_item_time_period(item: exchangelib.CalendarItem) -> TimePeriod:
    def ews_datetime_to_timestamp(
        ews: exchangelib.items.calendar_item.DateOrDateTimeField,
    ) -> TimeStamp:
        dt: datetime

        # TODO(metafates): not sure about it... need to check if it works
        if isinstance(ews, exchangelib.EWSDateTime):
            dt = datetime(
                year=ews.year,
                month=ews.month,
                day=ews.month,
                hour=ews.hour,
                minute=ews.minute,
            )
        elif isinstance(ews, exchangelib.EWSDate):
            dt = datetime(
                year=ews.year,
                month=ews.month,
                day=ews.month,
            )
        else:
            # TODO(metafates): improve these error messages
            raise Exception("unknown ews date instance")

        return TimeStamp(
            datetime_utc=dt,
        )

    if item.start is None:
        # TODO(metafates): improve these error messages
        raise Exception("start missing")

    if item.end is None:
        # TODO(metafates): improve these error messages
        raise Exception("end is missing")

    start = ews_datetime_to_timestamp(item.start)
    end = ews_datetime_to_timestamp(item.end)

    return TimePeriod(start, end)


def calendar_item_room(item: exchangelib.CalendarItem) -> Room:
    # Here we have to deal with two cases
    #
    # 1. Sometimes room is in `resources` field (makes sense)
    # 2. Sometimes it is in the `required_attendees` field (oh god why????)

    attendee: exchangelib.Attendee

    assert item.resources is None or isinstance(
        item.resources, collections.abc.Sequence
    )

    assert item.required_attendees is None or isinstance(
        item.required_attendees, collections.abc.Sequence
    )

    if (resources := item.resources) is not None and len(resources):
        # Usually, there's only one item in resources list
        attendee = resources[0]
    elif (attendees := item.required_attendees) is not None and len(attendees):
        # Usually, if the room itself is placed as the last attendee.
        attendee = attendees[-1]
    else:
        raise Exception("no room specified")

    mailbox = attendee.mailbox

    assert mailbox is not None and isinstance(mailbox, exchangelib.Mailbox)
    email_address = mailbox.email_address

    email = str(email_address)

    return Room(email=email, name_en="", name_ru="")


def calendar_item_to_booking(item: exchangelib.CalendarItem) -> BookingWithId:
    id = item.id
    if id is None:
        # TODO(metafates): improve these error messages
        raise Exception("id is missing")

    id = BookingId(id)

    subject = item.subject
    if subject is None:
        # TODO(metafates): improve these error messages
        raise Exception("subject is missing")

    title = str(subject)

    owner = calendar_item_owner(item)
    period = calendar_item_time_period(item)
    room = calendar_item_room(item)

    return BookingWithId(
        id=id,
        owner=owner,
        period=period,
        title=title,
        room=room,
    )


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
            required_attendees=[booking.owner.email, booking.room.email],
        )

        item.save(send_meeting_invitations=exchangelib.items.SEND_ONLY_TO_ALL)

        if item.id is None:
            # TODO(metafates): make error make informational
            raise Exception("id is none")

        return item.id

    async def delete_booking(self, booking_id: BookingId):
        booking = self._account.calendar.get(id=booking_id)  # type: ignore
        booking.delete()

    async def get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        items_in_period = self._account.calendar.filter(  # type: ignore
            start__range=(period.start.datetime, period.end.datetime)
        )

        bookings: list[BookingWithId] = []

        for item in items_in_period:
            assert isinstance(item, exchangelib.CalendarItem)

            booking = calendar_item_to_booking(item)

            if filter_rooms is not None and booking.room not in filter_rooms:
                continue

            if (
                filter_user_email is not None
                and booking.owner.email != filter_user_email
            ):
                continue

            bookings.append(booking)

        return bookings

    async def get_booking_owner(self, booking_id: BookingId) -> User:
        calendar_item = self._account.calendar.get(id=booking_id)  # type: ignore
        return calendar_item_owner(calendar_item)
