from typing import Annotated

import exchangelib
import exchangelib.errors
from fastapi import APIRouter, Depends, status, HTTPException

from app.api.dependencies import locale
from app.api.iam.dependencies import authenticated_user
from .api_exceptions.such_room_does_not_exist_error import SuchRoomDoesNotExistError
from .outlook_adapter import adapter
from .schemas import (
    GetFreeRoomsRequest,
    QueryBookingsRequest,
    RoomSchema,
    BookingWithIdSchema
)
from ...config import bookable_rooms
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
    tags=["Common Methods"],
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
async def get_free_rooms(
        req: GetFreeRoomsRequest,
        language: Annotated[Language, Depends(locale)]
) -> list[RoomSchema]:
    bookings = await adapter.get_bookings_in_period(
        period=TimePeriod(
            start=TimeStamp(req.start.timestamp()),
            end=TimeStamp(req.end.timestamp())))
    return list(map(lambda booking: BookingWithIdSchema.from_booking_with_id(booking, language).room, bookings))


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
                start=TimeStamp(req.filter.started_at_or_after.timestamp()),
                end=TimeStamp(req.filter.ended_at_or_before.timestamp())
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
