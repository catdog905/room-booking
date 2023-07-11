from fastapi import APIRouter, Depends, status

from app.api.dependencies import locale
from app.api.iam.dependencies import authenticated_user
from typing import Annotated

import exchangelib
import exchangelib.errors
from fastapi import APIRouter, Depends, status, HTTPException

from .api_exceptions.such_room_does_not_exist_error import SuchRoomDoesNotExistError
from .schemas import (
    Booking,
    BookRoomError,
    BookRoomRequest,
    GetFreeRoomsRequest,
    QueryBookingsRequest,
    RoomSchema,
    BookingWithIdSchema,
    Room,
)
from ..deps import auth, locale
from ...adapters.outlook import OutlookBookings, RoomsRegistry
from ...config import bookable_rooms
from ...config import config
from ...domain.entities.booking import Booking, BookingWithId
from ...domain.entities.common import Language
from ...domain.entities.exceptions.end_time_before_start_time_exception import EndTimeBeforeStartTimeException
from ...domain.entities.iam import User
from ...domain.entities.time.time_period import TimePeriod
from ...domain.entities.time.time_stamp import TimeStamp

unauthorized_responses: dict[int | str, dict[str, str]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "API token was not provided, is invalid or has been expired",
    }
}

router = APIRouter(
    tags=["Booking"],
    dependencies=[Depends(locale), Depends(authenticated_user)],
    responses=unauthorized_responses,
)

credentials = exchangelib.OAuth2Credentials(
    client_id=config.app_client_id,
    client_secret=config.app_secret,
    tenant_id=config.app_tenant_id,
    identity=exchangelib.Identity(primary_smtp_address=config.outlook_email),
)
server_config = exchangelib.Configuration(
    server="outlook.office365.com",
    credentials=credentials,
    auth_type=exchangelib.OAUTH2,
)
account = exchangelib.Account(
    primary_smtp_address=config.outlook_email,
    config=server_config,
    autodiscover=False,
    access_type=exchangelib.DELEGATE,
)
adapter = OutlookBookings(
    account=account,
    account_config=server_config,
    rooms_registry=RoomsRegistry(bookable_rooms),
    executor=None
)


@router.get(
    "/rooms",
    name="Get all bookable rooms",
    operation_id="get_rooms",
)
async def get_rooms(
        language: Annotated[Language, Depends(locale)]
) -> list[RoomSchema]:
    return list(map(lambda room: RoomSchema.from_room(room, language), bookable_rooms))


@router.post(
    "/rooms/free",
    name="Get free rooms",
    operation_id="get_free_rooms",
    description="Returns a list of rooms that are available for booking at the"
                " specified time period.",
)
async def get_free_rooms(
        req: GetFreeRoomsRequest,
        language: Annotated[Language, Depends(locale)]
) -> list[RoomSchema]:
    bookings = await adapter.get_bookings_in_period(
        period=TimePeriod(
            start=TimeStamp(req.start),
            end=TimeStamp(req.end)))
    return list(map(lambda booking: BookingWithIdSchema.from_booking_with_id(booking, language).room, bookings))


@router.post(
    "/rooms/{room_id}/book",
    name="Book a room",
    operation_id="book_room",
    responses={
        status.HTTP_200_OK: {
            "description": "Room has been booked successfully",
            "model": BookingWithIdSchema,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "This room cannot be booked for this user during"
                           " this time period",
            "model": BookRoomError,
        },
    },
)
async def book_room(
        room_id: str,
        req: BookRoomRequest,
        language: Annotated[Language, Depends(locale)]
) -> BookingWithIdSchema:
    try:
        booking = Booking(title=req.title,
                          period=TimePeriod(
                              TimeStamp(req.start),
                              TimeStamp(req.end)),
                          room=[room for room in bookable_rooms if room.id == room_id][0],
                          owner=User(req.owner_email))
    except IndexError as exception:
        raise SuchRoomDoesNotExistError(room_id=room_id) from exception
    booking_id = await adapter.create_booking(booking)
    # ATTENTION: strange things here
    #   BookingWithId instantiated from different sources: booking from user input and id from outlook_api
    booking_with_id = BookingWithId.from_booking_and_id(booking, booking_id)
    return BookingWithIdSchema.from_booking_with_id(booking_with_id, language)


@router.get(
    "/bookings/my",
    name="Get my bookings",
    operation_id="get_my_bookings",
    description="Returns a list of bookings for the requesting user.",
)
async def get_my_bookings() -> list[BookingWithIdSchema]:
    raise NotImplementedError  # need to implement necessary method in adapter first


@router.post(
    "/bookings/query",
    name="Query bookings",
    operation_id="query_bookings",
)
async def query_bookings(
        req: QueryBookingsRequest,
        language: Annotated[Language, Depends(locale)]
) -> list[BookingWithIdSchema]:
    filter_rooms = None
    if req.filter.room_id_in is not None:
        filter_rooms = []
        for room_id in req.filter.room_id_in:
            try:
                filter_rooms.append([room for room in bookable_rooms if room.id == room_id][0])
            except IndexError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=str(SuchRoomDoesNotExistError(room_id=room_id)))
    try:
        bookings_with_id = await adapter.get_bookings_in_period(
            period=TimePeriod(
                start=TimeStamp(req.filter.started_at_or_after),
                end=TimeStamp(req.filter.ended_at_or_before)
            ),
            filter_rooms=filter_rooms
        )
    except exchangelib.errors.ErrorCalendarViewRangeTooBig as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exception))
    except EndTimeBeforeStartTimeException as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exception))
    if req.filter.owner_email_in is not None:
        bookings_with_id = [booking for booking in bookings_with_id if booking.owner.email in req.filter.owner_email_in]
    return [BookingWithIdSchema.from_booking_with_id(booking_with_id, language) for booking_with_id in bookings_with_id]


@router.delete(
    "/bookings/{booking_id}",
    name="Delete a booking",
    operation_id="delete_booking",
    responses={
        status.HTTP_200_OK: {
            "description": "Booking was deleted successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Booking with such ID is not found",
        },
    },
)
async def delete_booking(booking_id: str) -> None:
    await adapter.delete_booking(booking_id)
