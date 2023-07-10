import asyncio
import datetime
import random
from os import getenv
from re import finditer
from uuid import uuid4

import exchangelib
import pytest

from app.adapters.outlook import OutlookBookings, RoomsRegistry
from app.domain.entities.booking import (
    Booking,
    BookingId,
    Room,
    TimePeriod,
    TimeStamp,
    User,
)

EMAIL = getenv("EMAIL")
APP_TENANT_ID = getenv("APP_TENANT_ID")
APP_CLIENT_ID = getenv("APP_CLIENT_ID")
APP_SECRET = getenv("APP_SECRET")
APP_SECRET_ID = getenv("APP_SECRET_ID")

credentials = exchangelib.OAuth2Credentials(
    client_id=APP_CLIENT_ID,
    client_secret=APP_SECRET,
    tenant_id=APP_TENANT_ID,
    identity=exchangelib.Identity(primary_smtp_address=EMAIL),
)

account_config = exchangelib.Configuration(
    server="outlook.office365.com",
    credentials=credentials,
    auth_type=exchangelib.OAUTH2,
)

account = exchangelib.Account(
    primary_smtp_address=EMAIL,
    config=account_config,
    autodiscover=False,
    access_type=exchangelib.DELEGATE,
)

rooms = [
    Room(
        "iu.resource.lectureroom313@0f4tw.onmicrosoft.com",
        "University Room #313",
        "Комната #313",
    ),
    Room(
        "iu.resource.lectureroom314@0f4tw.onmicrosoft.com",
        "University Room #314",
        "Комната #314",
    ),
    Room(
        "iu.resource.lectureroom318@0f4tw.onmicrosoft.com",
        "University Room #318",
        "Комната #318",
    ),
]

rooms_registry = RoomsRegistry(rooms)

adapter = OutlookBookings(
    account=account,
    account_config=account_config,
    rooms_registry=rooms_registry,
    executor=None,
)


def random_time_period() -> TimePeriod:
    start_date = datetime.datetime.now() + datetime.timedelta(days=random.randint(0, 7))

    # Generate a random number of minutes (divisible by 5)
    minutes = random.randint(0, 11) * 5

    # Set the minutes of the start date
    start_date = start_date.replace(minute=minutes)

    # Generate a random end date with no more than 3 hours difference
    minutes = random.randint(0, 11 * 3) * 5
    end_date = start_date + datetime.timedelta(minutes=minutes)

    return TimePeriod(TimeStamp(start_date), TimeStamp(end_date))


def test_booking_create_and_delete():
    owner = User("user@example.com")
    period = random_time_period()
    room = random.choice(rooms)
    booking = Booking(
        title=f"Test Booking {uuid4().hex}",
        period=period,
        room=random.choice(rooms),
        owner=owner,
    )

    booking_id = adapter.create_booking_blocking(booking)

    assert owner.email == adapter.get_booking_owner_blocking(booking_id).email

    bookings_in_period = adapter.get_bookings_in_period_blocking(
        period=period, filter_rooms=[room], filter_user_email=owner.email
    )

    assert len(bookings_in_period) >= 1
    assert booking_id in map(lambda b: b.id, bookings_in_period)

    adapter.delete_booking_blocking(booking_id)

    with pytest.raises(Exception):
        adapter.delete_booking_blocking(booking_id)
