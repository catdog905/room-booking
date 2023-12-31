from app.domain.dependencies.bookings_repo import BookingsRepo
from app.domain.entities import BookingId, Room, User


async def book_room_for_user(
    repo: BookingsRepo,
    room: Room,
    user: User,
) -> BookingId:
    ...


async def delete_booking_by_user(
    repo: BookingsRepo,
    booking_id: BookingId,
    user: User,
):
    # 1. Try to find booking
    #   a. Not found -> raise exception "not-found"
    # 2. Get booking owner
    #   a. User is not owner -> raise exception "permission-error"
    # 3. Is booking in the past?
    #   Yes -> raise exception "invalid"
    #   No  -> OK, delete booking
    ...
