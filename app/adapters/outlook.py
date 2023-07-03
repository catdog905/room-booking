__all__ = ["OutlookBookings", "RoomsRegistry"]

import asyncio
import collections.abc
import concurrent.futures
from datetime import datetime
from logging import getLogger
from typing import TypedDict, Unpack

import exchangelib
import exchangelib.recurrence
from exchangelib.fields import AttendeesField

from app.domain.dependencies import BookingsRepo
from app.domain.entities import (
    Booking,
    BookingId,
    BookingWithId,
    Language,
    Room,
    TimePeriod,
    TimeStamp,
    User,
)

DEFAULT_BOOKING_TITLE = "Untitled"
LEGACY_BOOKING_SYSTEM_EMAIL = "TODO"

logger = getLogger(__name__)


class InvalidCalendarItemError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MissingCalendarItemFieldError(InvalidCalendarItemError):
    def __init__(self, field: str) -> None:
        super().__init__(f"Missing field: {field}")


class RoomsRegistry:
    _rooms_by_email_map: dict[str, Room]
    _rooms_by_name_map: dict[str, Room]

    def __init__(self, rooms: list[Room]):
        self._rooms_by_email_map = {}
        self._rooms_by_name_map = {}

        for room in rooms:
            self._rooms_by_email_map[room.email] = room
            for language in Language:
                self._rooms_by_name_map[room.get_name(language)] = room

    def get_by_email(self, email: str) -> Room | None:
        return self._rooms_by_email_map.get(email)

    def get_by_name(self, name: str) -> Room | None:
        return self._rooms_by_name_map.get(name)


class BookingsDict(TypedDict):
    account: exchangelib.Account
    account_config: exchangelib.Configuration
    rooms_registry: RoomsRegistry
    executor: concurrent.futures.ThreadPoolExecutor | None


class OutlookBookings(BookingsRepo):
    def __init__(self, **kwargs: Unpack[BookingsDict]):
        self._account = kwargs["account"]
        self._account_config = kwargs["account_config"]
        self._rooms = kwargs["rooms_registry"]

        executor = kwargs["executor"]
        if executor is None:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self._executor = executor

    async def create_booking(self, booking: Booking) -> BookingId:
        return await asyncio.get_running_loop().run_in_executor(
            self._executor,
            self.create_booking_blocking,
            booking,
        )

    def create_booking_blocking(self, booking: Booking) -> BookingId:
        item = exchangelib.CalendarItem(
            account=self._account,
            folder=self._account.calendar,
            start=booking.period.start.datetime,
            end=booking.period.end.datetime,
            subject=booking.title,
            location=booking.room.get_name(Language.EN),
            body=f"Booking on request from {booking.owner.email}",
            required_attendees=[
                exchangelib.Attendee(
                    mailbox=exchangelib.Mailbox(email_address=booking.owner.email),
                    response_type="Organizer",
                ),
                exchangelib.Attendee(
                    mailbox=exchangelib.Mailbox(email_address=booking.room.email),
                ),
            ],
        )

        # After this operation the ID will be set
        item.save(send_meeting_invitations=exchangelib.items.SEND_ONLY_TO_ALL)

        if item.id is None:
            # I'm not sure if such situation is possible, but just in case.
            #
            # If after saving a booking id wasn't set somehow
            # we should undo the booking.
            try:
                item.delete()
            except Exception as e:
                logger.warning(f"Error while reverting booking: {e}")

            raise MissingCalendarItemFieldError("id")

        return item.id

    async def delete_booking(self, booking_id: BookingId):
        return await asyncio.get_running_loop().run_in_executor(
            self._executor,
            self.delete_booking_blocking,
            booking_id,
        )

    def delete_booking_blocking(self, booking_id: BookingId):
        # TODO(metafates): assertion magic so that pyright will stop complaining about this
        booking = self._account.calendar.get(id=booking_id)  # type: ignore
        booking.delete()

    async def get_bookings_in_period(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        return await asyncio.get_running_loop().run_in_executor(
            self._executor,
            self.get_bookings_in_period_blocking,
            period,
            filter_rooms,
            filter_user_email,
        )

    def get_bookings_in_period_blocking(
        self,
        period: TimePeriod,
        filter_rooms: list[Room] | None = None,
        filter_user_email: str | None = None,
    ) -> list[BookingWithId]:
        # TODO(metafates): assertion magic so that pyright will stop complaining about this
        items_in_period: list[exchangelib.CalendarItem] = list(
            self._account.calendar.view(  # type: ignore
                start=period.start.datetime, end=period.end.datetime
            )
        )

        # FIXME(metafates): this is a super dumb and slow solution just to get the idea
        if filter_rooms is not None:
            for room, account in zip(
                filter_rooms,
                map(self._get_ews_account_for_room, filter_rooms),
            ):
                logger.info(
                    f"Getting calendar items for room {room.get_name(Language.EN)}"
                )
                items = account.calendar.view(  # type: ignore
                    start=period.start.datetime,
                    end=period.end.datetime,
                ).all()
                items_in_period.extend(items)

        bookings: list[BookingWithId] = []
        bookings_ids: set[str] = set()

        for item in items_in_period:
            try:
                booking = convert_calendar_item_to_booking_with_id(item, self._rooms)
            except InvalidCalendarItemError as e:
                logger.warning(f"Invalid calendar item: {e}")
                continue

            if (
                filter_user_email is not None
                and booking.owner.email != filter_user_email
            ):
                continue

            if booking.id in bookings_ids:
                continue

            bookings_ids.add(booking.id)
            bookings.append(booking)

        return bookings

    async def get_booking_owner(self, booking_id: BookingId) -> User:
        return await asyncio.get_running_loop().run_in_executor(
            self._executor,
            self.get_booking_owner_blocking,
            booking_id,
        )

    def get_booking_owner_blocking(self, booking_id: BookingId) -> User:
        # TODO(metafates): assertion magic so that pyright will stop complaining about this
        calendar_item = self._account.calendar.get(id=booking_id)  # type: ignore
        return get_calendar_item_owner(calendar_item)

    def _get_ews_account_for_room(self, room: Room) -> exchangelib.Account:
        # Just to make sure
        assert self._rooms.get_by_email(room.email) is not None

        return exchangelib.Account(
            primary_smtp_address=room.email,
            config=self._account_config,
            autodiscover=False,
            access_type=exchangelib.IMPERSONATION,
        )


def convert_calendar_item_to_booking_with_id(
    item: exchangelib.CalendarItem,
    rooms_registry: RoomsRegistry,
) -> BookingWithId:
    if item.id is None:
        raise MissingCalendarItemFieldError("id")

    owner = get_calendar_item_owner(item)
    period = get_calendar_item_time_period(item)
    room = get_calendar_item_room(item, rooms_registry)

    return BookingWithId(
        id=BookingId(item.id),
        title=str(item.subject) or DEFAULT_BOOKING_TITLE,
        owner=owner,
        period=period,
        room=room,
    )


def get_calendar_item_organizer_email(item: exchangelib.CalendarItem) -> str | None:
    assert item.required_attendees is None or isinstance(
        item.required_attendees,
        collections.abc.Sequence,
    )

    assert item.organizer is None or isinstance(
        item.organizer,
        exchangelib.Mailbox,
    )

    if (organizer := item.organizer) is not None:
        return str(organizer.email_address)

    if (attendees := item.required_attendees) is not None and len(attendees) > 0:
        organizer_email: str | None = None
        for attendee in attendees:
            assert isinstance(attendee, exchangelib.Attendee)

            if attendee.response_type == "Organizer":
                assert isinstance(attendee.mailbox, exchangelib.Mailbox)

                email = attendee.mailbox.email_address

                if organizer_email is not None:
                    return None

                organizer_email = str(email)

        return organizer_email

    return None


def get_calendar_item_owner(item: exchangelib.CalendarItem) -> User:
    # The problem is that old booking services may appear as organizers,
    # so we try to filter them out and get the real owner.

    organizer_email = get_calendar_item_organizer_email(item)

    if organizer_email is None:
        raise MissingCalendarItemFieldError("owner")

    if organizer_email != LEGACY_BOOKING_SYSTEM_EMAIL:
        return User(organizer_email)

    attendees = item.required_attendees

    if attendees is None:
        raise MissingCalendarItemFieldError("owner")

    assert isinstance(attendees, collections.abc.Sequence)

    attendee = attendees[0]
    assert isinstance(attendee, exchangelib.Attendee) and isinstance(
        attendee.mailbox, exchangelib.Mailbox
    )
    if str(attendee.mailbox.email_address) != LEGACY_BOOKING_SYSTEM_EMAIL:
        raise MissingCalendarItemFieldError("owner")

    if len(attendees) < 2:
        raise MissingCalendarItemFieldError("owner")

    attendee = attendees[1]
    assert isinstance(attendee, exchangelib.Attendee) and isinstance(
        attendee.mailbox, exchangelib.Mailbox
    )

    return User(str(attendee.mailbox.email_address))


def get_calendar_item_time_period(item: exchangelib.CalendarItem) -> TimePeriod:
    if item.start is None:
        # TODO(metafates): improve these error messages
        raise MissingCalendarItemFieldError("start")

    if item.end is None:
        # TODO(metafates): improve these error messages
        raise MissingCalendarItemFieldError("end")

    return TimePeriod(
        start=convert_ews_date_or_time_to_time_stamp(item.start),
        end=convert_ews_date_or_time_to_time_stamp(item.end),
    )


def get_calendar_item_room(
    item: exchangelib.CalendarItem,
    rooms_registry: RoomsRegistry,
) -> Room:
    # Here we have to deal with two cases
    #
    # 1. Room is in the `resources` field
    # 2. Room is in the `required_attendees` field

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

            if (room := rooms_registry.get_by_email(email)) is not None:
                return room

    if (attendees := item.required_attendees) is not None and len(attendees):
        for attendee in attendees:
            assert isinstance(attendee, exchangelib.Attendee)

            mailbox = attendee.mailbox
            assert mailbox is not None and isinstance(mailbox, exchangelib.Mailbox)

            email = str(mailbox.email_address)

            if (room := rooms_registry.get_by_email(email)) is not None:
                return room

    raise MissingCalendarItemFieldError("room")


def convert_ews_date_or_time_to_time_stamp(
    ews: exchangelib.items.calendar_item.DateOrDateTimeField,
) -> TimeStamp:
    if isinstance(ews, exchangelib.EWSDateTime):
        return TimeStamp(
            datetime_utc=datetime(
                year=ews.year,
                month=ews.month,
                day=ews.day,
                hour=ews.hour,
                minute=ews.minute,
            )
        )

    if isinstance(ews, exchangelib.EWSDate):
        return TimeStamp(
            datetime_utc=datetime(
                year=ews.year,
                month=ews.month,
                day=ews.day,
                hour=0,
                minute=0,
            )
        )

    raise InvalidCalendarItemError("Unknown date type")
