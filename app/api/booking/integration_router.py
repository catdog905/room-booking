from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException

from app.api.dependencies import locale
from app.api.iam.dependencies import authenticated_user
from .api_exceptions.such_room_does_not_exist_error import SuchRoomDoesNotExistError
from .outlook_adapter import adapter
from .schemas import (
    BookRoomError,
    BookRoomRequest,
    BookingWithIdSchema
)
from ...config import bookable_rooms
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
    tags=["Integrations Booking"],
    responses=unauthorized_responses,
)


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
        language: Annotated[Language, Depends(locale)],
        user: Annotated[User, Depends(authenticated_user)]
) -> BookingWithIdSchema:
    try:
        booking = Booking(title=req.title,
                          period=TimePeriod(
                              TimeStamp(req.start.timestamp()),
                              TimeStamp(req.end.timestamp())),
                          room=[room for room in bookable_rooms if room.id == room_id][0],
                          owner=user)
    except IndexError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(SuchRoomDoesNotExistError(room_id=room_id)))
    except EndTimeBeforeStartTimeException as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(exception))
    booking_id = await adapter.create_booking(booking)
    # ATTENTION: strange things here
    #   BookingWithId instantiated from different sources: booking from user input and id from outlook_api
    booking_with_id = BookingWithId.from_booking_and_id(booking, booking_id)
    return BookingWithIdSchema.from_booking_with_id(booking_with_id, language)


@router.delete(
    "/bookings/{booking_id}",
    name="Delete a booking",
    operation_id="delete_booking",
    responses={
        status.HTTP_200_OK: {
            "description": "Booking was deleted successfully",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User have no such permission",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Booking with such ID is not found",
        },
    },
)
async def delete_booking(
        booking_id: str,
        user: Annotated[User, Depends(authenticated_user)]
) -> None:
    try:
        booking_user = adapter.get_booking_owner_blocking(booking_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Booking with such ID is not found')
    print(str(booking_user))
    if user != booking_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User have no such permission')
    await adapter.delete_booking(booking_id)
