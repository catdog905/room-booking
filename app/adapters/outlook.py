import concurrent.futures
import asyncio
import logging
import re
import exchangelib
import exchangelib.recurrence
import collections.abc
from datetime import datetime

import app.domain.dependencies.bookable as bookable

from app.domain.entities import Booking, TimePeriod, Room, User
from app.domain.dependencies import BookingsRepo
from app.domain.entities.booking import BookingId, BookingWithId, TimeStamp
from app.domain.entities.common import Language


class InvalidCalendarItemException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MissingCalendarItemFieldException(InvalidCalendarItemException):
    def __init__(self, field: str) -> None:
        super().__init__(f"Missing field: {field}")


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

    assert item.required_attendees is None or isinstance(
        item.required_attendees, collections.abc.Sequence
    )

    assert item.organizer is None or isinstance(item.organizer, exchangelib.Mailbox)

    mailbox: exchangelib.Mailbox
    if (attendees := item.required_attendees) is not None and len(attendees):
        attendee: exchangelib.Attendee
        if len(attendees) > 1:
            attendee = attendees[1]
        else:
            attendee = attendees[0]

        assert isinstance(attendee.mailbox, exchangelib.Mailbox)
        mailbox = attendee.mailbox
    elif (organizer := item.organizer) is not None:
        mailbox = organizer
    else:
        raise MissingCalendarItemFieldException("owner")

    email_address = str(mailbox.email_address)
    return User(email_address)


def calendar_item_time_period(item: exchangelib.CalendarItem) -> TimePeriod:
    def ews_datetime_to_timestamp(
        ews: exchangelib.items.calendar_item.DateOrDateTimeField,
    ) -> TimeStamp:
        if isinstance(ews, exchangelib.EWSDateTime):
            return TimeStamp(
                datetime_utc=datetime(
                    year=ews.year,
                    month=ews.month,
                    day=ews.month,
                    hour=ews.hour,
                    minute=ews.minute,
                )
            )

        if isinstance(ews, exchangelib.EWSDate):
            return TimeStamp(
                datetime_utc=datetime(
                    year=ews.year,
                    month=ews.month,
                    day=ews.month,
                )
            )

        raise InvalidCalendarItemException("Unknown date type")

    if item.start is None:
        # TODO(metafates): improve these error messages
        raise MissingCalendarItemFieldException("start")

    if item.end is None:
        # TODO(metafates): improve these error messages
        raise MissingCalendarItemFieldException("end")

    start = ews_datetime_to_timestamp(item.start)
    end = ews_datetime_to_timestamp(item.end)

    return TimePeriod(start, end)


def calendar_item_room(item: exchangelib.CalendarItem) -> Room:
    # Here we have to deal with two cases
    #
    # 1. Sometimes room is in `resources` field (makes sense)
    # 2. Sometimes it's in the `required_attendees` field (oh god why????)
    # 3. And... sometimes it's in the `location` without any further information

    assert item.resources is None or isinstance(
        item.resources, collections.abc.Sequence
    )

    assert item.required_attendees is None or isinstance(
        item.required_attendees, collections.abc.Sequence
    )

    if (resources := item.resources) is not None and len(resources):
        for resource in resources:
            assert isinstance(resource, exchangelib.Attendee)

            mailbox = resource.mailbox
            assert mailbox is not None and isinstance(mailbox, exchangelib.Mailbox)

            email = str(mailbox.email_address)

            if (room := bookable.ROOMS.get_by_email(email)) is not None:
                return Room.from_bookable_room(room)

    if (attendees := item.required_attendees) is not None and len(attendees):
        # Usually, if the room itself is placed as the last attendee.
        for attendee in attendees:
            assert isinstance(attendee, exchangelib.Attendee)

            mailbox = attendee.mailbox
            assert mailbox is not None and isinstance(mailbox, exchangelib.Mailbox)

            email = str(mailbox.email_address)

            if (room := bookable.ROOMS.get_by_email(email)) is not None:
                return Room.from_bookable_room(room)

    if (location := item.location) is not None:
        name = str(location)

        if (room := bookable.ROOMS.get_by_name(name)) is not None:
            return Room.from_bookable_room(room)

    raise MissingCalendarItemFieldException("room")


def calendar_item_to_booking(item: exchangelib.CalendarItem) -> BookingWithId:
    id = item.id
    if id is None:
        raise MissingCalendarItemFieldException("id")

    id = BookingId(id)

    subject = item.subject
    if subject is None:
        # TODO(metafates): a better default value?
        subject = "No Subject"

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
    def __init__(
        self,
        account: exchangelib.Account,
        executor: concurrent.futures.ThreadPoolExecutor | None = None,
    ) -> None:
        self._account = account

        if executor is None:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        self._executor = executor

    async def create_booking(self, booking: Booking) -> BookingId:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._create_booking, booking)

    def _create_booking(self, booking: Booking) -> BookingId:
        # TODO(metafates): add proper fields

        # Here we try to satisfy all legacy systems
        item = exchangelib.CalendarItem(
            account=self._account,
            folder=self._account.calendar,
            start=booking.period.start.datetime,
            end=booking.period.end.datetime,
            subject=booking.title,
            location=booking.room.get_name(Language.EN),
            required_attendees=[
                exchangelib.Attendee(
                    mailbox=exchangelib.Mailbox(
                        email_address=self._account.primary_smtp_address
                    )
                ),
                exchangelib.Attendee(
                    mailbox=exchangelib.Mailbox(email_address=booking.owner.email),
                    response_type="Accept",
                ),
                exchangelib.Attendee(
                    mailbox=exchangelib.Mailbox(email_address=booking.room.email),
                ),
            ],
        )

        # After this operation the ID will be set
        item.save(send_meeting_invitations=exchangelib.items.SEND_ONLY_TO_ALL)

        if item.id is None:
            # I'm not sure if such sitation is possible, but just in case.
            #
            # If after saving a booking id wasn't set somehow
            # we should undo the booking.
            try:
                item.delete()
            except Exception as e:
                logging.warn(f"Error while reverting booking: {e}")

            raise MissingCalendarItemFieldException("id")

        return item.id

    async def delete_booking(self, booking_id: BookingId):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._delete_booking, booking_id
        )

    def _delete_booking(self, booking_id: BookingId):
        # TODO(metafates): assertion magic so that pyright will stop complaining about this
        booking = self._account.calendar.get(id=booking_id)  # type: ignore
        booking.delete()

    async def get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._get_bookings_in_period,
            period,
            filter_rooms,
            filter_user_email,
        )

    def _get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        # TODO(metafates): assertion magic so that pyright will stop complaining about this
        items_in_period = self._account.calendar.filter(  # type: ignore
            start__range=(period.start.datetime, period.end.datetime)
        )

        bookings: list[BookingWithId] = []

        for item in items_in_period:
            assert isinstance(item, exchangelib.CalendarItem)

            try:
                booking = calendar_item_to_booking(item)
            except InvalidCalendarItemException as e:
                logging.warn(f"Invalid calendar item: {e}")
                continue

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
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._get_booking_owner, booking_id
        )

    def _get_booking_owner(self, booking_id: BookingId) -> User:
        # TODO(metafates): assertion magic so that pyright will stop complaining about this
        calendar_item = self._account.calendar.get(id=booking_id)  # type: ignore
        return calendar_item_owner(calendar_item)
