import concurrent
from typing import Annotated

import exchangelib
from fastapi import APIRouter, Depends, status

from ...adapters.outlook import OutlookBookings, RoomsRegistry
from ...config import config
from ...config import bookable_rooms
from ..deps import auth, locale
from .schemas import (
    Booking,
    BookRoomError,
    BookRoomRequest,
    GetFreeRoomsRequest,
    QueryBookingsRequest,
    RoomSchema,
)
from ...domain.entities import Language, Room, TimePeriod, TimeStamp

unauthorized_responses: dict[int | str, dict[str, str]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "API token was not provided, is invalid or has been expired",
    }
}

router = APIRouter(
    tags=["Booking"],
    dependencies=[Depends(locale), Depends(auth)],
    responses=unauthorized_responses,
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
async def get_free_rooms(req: GetFreeRoomsRequest, language: Annotated[Language, Depends(locale)]) -> list[RoomSchema]:
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
    bookings = await adapter.get_bookings_in_period(period=TimePeriod(
        start=TimeStamp(req.start),
        end=TimeStamp(req.end)))
    print(list(map(lambda booking: booking.__dict__, bookings)))
    return "hello"


@router.post(
    "/rooms/{room_id}/book",
    name="Book a room",
    operation_id="book_room",
    responses={
        status.HTTP_200_OK: {
            "description": "Room has been booked successfully",
            "model": Booking,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "This room cannot be booked for this user during"
                           " this time period",
            "model": BookRoomError,
        },
    },
)
async def book_room(room_id: str, req: BookRoomRequest) -> Booking:
    raise NotImplementedError


@router.get(
    "/bookings/my",
    name="Get my bookings",
    operation_id="get_my_bookings",
    description="Returns a list of bookings for the requesting user.",
)
async def get_my_bookings() -> list[Booking]:
    raise NotImplementedError


@router.post(
    "/bookings/query",
    name="Query bookings",
    operation_id="query_bookings",
)
async def query_bookings(req: QueryBookingsRequest) -> list[Booking]:
    raise NotImplementedError


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
    raise NotImplementedError
