import concurrent.futures
import asyncio
import logging
from typing import TypedDict, Unpack
import exchangelib
import exchangelib.recurrence
import collections.abc
from datetime import datetime

from app.domain.dependencies import BookingsRepo

from app.domain.entities import Booking, TimePeriod, Room, User
from app.domain.entities.booking import BookingId, BookingWithId, TimeStamp
from app.domain.entities.common import Language


class InvalidCalendarItemError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MissingCalendarItemFieldError(InvalidCalendarItemError):
    def __init__(self, field: str) -> None:
        super().__init__(f"Missing field: {field}")


class _Rooms:
    """
    The efficient way to get/check rooms by email or name.
    All operations are done in O(1)
    """

    _email = str
    _name = str

    _rooms_dict_email: dict[_email, Room]
    _rooms_dict_name: dict[_name, Room]
    _rooms_list: list[Room]

    def __init__(self, rooms: list[Room]) -> None:
        self._rooms_dict_email = {}
        self._rooms_dict_name = {}
        self._rooms_list = rooms

        for room in rooms:
            self._rooms_dict_email[room.email] = room
            for language in Language:
                self._rooms_dict_name[room.get_name(language)] = room

    def get_by_email(self, email: _email) -> Room | None:
        return self._rooms_dict_email.get(email)

    def get_by_name(self, name: str) -> Room | None:
        return self._rooms_dict_name.get(name)


class Config(TypedDict):
    account: exchangelib.Account
    account_config: exchangelib.Configuration
    bookable_rooms: list[Room]
    executor: concurrent.futures.ThreadPoolExecutor | None


class Adapter(BookingsRepo):
    def __init__(self, **kwargs: Unpack[Config]) -> None:
        self._account = kwargs["account"]
        self._account_config = kwargs["account_config"]
        self._bookable_rooms = _Rooms(kwargs["bookable_rooms"])

        executor = kwargs["executor"]

        if executor is None:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        self._executor = executor

    async def create_booking(self, booking: Booking) -> BookingId:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._create_booking, booking)

    def _create_booking(self, booking: Booking) -> BookingId:
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
            # I'm not sure if such sitation is possible, but just in case.
            #
            # If after saving a booking id wasn't set somehow
            # we should undo the booking.
            try:
                item.delete()
            except Exception as e:
                logging.warn(f"Error while reverting booking: {e}")

            raise MissingCalendarItemFieldError("id")

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
        items_in_period: list[exchangelib.CalendarItem] = list(
            self._account.calendar.view(  # type: ignore
                start=period.start.datetime, end=period.end.datetime
            )
        )

        def get_ews_account_for_room(room: Room) -> exchangelib.Account:
            # Just to make sure
            assert self._bookable_rooms.get_by_email(room.email) is not None

            return exchangelib.Account(
                primary_smtp_address=room.email,
                config=self._account_config,
                autodiscover=False,
                access_type=exchangelib.IMPERSONATION,
            )

        # FIXME(metafates): this is a super dumb and slow solution just to get the idea
        if filter_rooms is not None:
            for room, account in zip(
                filter_rooms, map(get_ews_account_for_room, filter_rooms)
            ):
                logging.info(
                    f"Getting calendar items for room {room.get_name(Language.EN)}"
                )
                items = account.calendar.view(start=period.start.datetime, end=period.end.datetime).all()  # type: ignore
                items_in_period.extend(items)

        bookings: list[BookingWithId] = []
        bookings_ids: set[str] = set()

        for item in items_in_period:
            try:
                booking = self._calendar_item_to_booking(item)
            except InvalidCalendarItemError as e:
                logging.warn(f"Invalid calendar item: {e}")
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
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._get_booking_owner, booking_id
        )

    def _get_booking_owner(self, booking_id: BookingId) -> User:
        # TODO(metafates): assertion magic so that pyright will stop complaining about this
        calendar_item = self._account.calendar.get(id=booking_id)  # type: ignore
        return self._calendar_item_owner(calendar_item)

    def _calendar_item_to_booking(
        self, item: exchangelib.CalendarItem
    ) -> BookingWithId:
        id = item.id
        if id is None:
            raise MissingCalendarItemFieldError("id")

        id = BookingId(id)

        subject = item.subject
        if subject is None:
            # TODO(metafates): a better default value?
            subject = "No Subject"

        title = str(subject)

        owner = self._calendar_item_owner(item)
        period = self._calendar_item_time_period(item)
        room = self._calendar_item_room(item)

        return BookingWithId(
            id=id,
            owner=owner,
            period=period,
            title=title,
            room=room,
        )

    def _calendar_item_owner(self, item: exchangelib.CalendarItem) -> User:
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

        if (attendees := item.required_attendees) is not None and len(attendees):
            owner: exchangelib.Attendee

            # Try to find owner by response type
            for attendee in attendees:
                if attendee.response_type == "Organizer":
                    owner = attendee
                    break
            else:  # if it fails, try to guess
                if len(attendees) > 1:
                    owner = attendees[1]
                else:
                    owner = attendees[0]

            assert isinstance(owner.mailbox, exchangelib.Mailbox)

            return User(str(owner.mailbox.email_address))

        if (organizer := item.organizer) is not None:
            return User(str(organizer.email_address))

        raise MissingCalendarItemFieldError("owner")

    def _calendar_item_time_period(self, item: exchangelib.CalendarItem) -> TimePeriod:
        def ews_datetime_to_timestamp(
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

        if item.start is None:
            # TODO(metafates): improve these error messages
            raise MissingCalendarItemFieldError("start")

        if item.end is None:
            # TODO(metafates): improve these error messages
            raise MissingCalendarItemFieldError("end")

        start = ews_datetime_to_timestamp(item.start)
        end = ews_datetime_to_timestamp(item.end)

        return TimePeriod(start, end)

    def _calendar_item_room(self, item: exchangelib.CalendarItem) -> Room:
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

                if (room := self._bookable_rooms.get_by_email(email)) is not None:
                    return room

        if (attendees := item.required_attendees) is not None and len(attendees):
            for attendee in attendees:
                assert isinstance(attendee, exchangelib.Attendee)

                mailbox = attendee.mailbox
                assert mailbox is not None and isinstance(mailbox, exchangelib.Mailbox)

                email = str(mailbox.email_address)

                if (room := self._bookable_rooms.get_by_email(email)) is not None:
                    return room

        raise MissingCalendarItemFieldError("room")
