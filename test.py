import asyncio
import concurrent.futures
import datetime

import exchangelib

import app.adapters.outlook
from app.domain.entities.booking import Booking, Room, TimePeriod, TimeStamp
from app.domain.entities.iam import User

EMAIL = "vladislav@0f4tw.onmicrosoft.com"

APP_TENANT_ID = "6f87849e-85b5-4661-ab58-ba9d87d3469a"
APP_CLIENT_ID = "c38ece28-3e8e-4dc8-88be-84b4d67cc843"
APP_SECRET = "lTn8Q~p_gAqeqwHR2pXp1NazJJttd7JJ~KI~1bfE"
APP_SECRET_ID = "55eaaa43-b240-46ef-9983-65b05e1658c4"

credentials = exchangelib.OAuth2Credentials(
    client_id=APP_CLIENT_ID,
    client_secret=APP_SECRET,
    tenant_id=APP_TENANT_ID,
    identity=exchangelib.Identity(primary_smtp_address=EMAIL),
)

config = exchangelib.Configuration(
    server="outlook.office365.com",
    credentials=credentials,
    auth_type=exchangelib.OAUTH2,
)

account = exchangelib.Account(
    primary_smtp_address=EMAIL,
    config=config,
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

# for item in account.calendar.all(): # type: ignore
#     print(f"Deleting item: {item.subject}")
#     item.delete()

outlook = app.adapters.outlook.OutlookBookings(
    account=account,
    account_config=config,
    executor=concurrent.futures.ThreadPoolExecutor(max_workers=5),
    rooms_registry=app.adapters.outlook.RoomsRegistry(rooms),
)

start = datetime.datetime(2023, 6, 27, 15)

# booking_id = asyncio.run(outlook.create_booking(Booking(
#     title="Test booking",
#     owner=User("booking.backend.api@0f4tw.onmicrosoft.com"),
#     room=rooms[0],
#     period=TimePeriod(TimeStamp(start), TimeStamp(start + datetime.timedelta(hours=2))),
# )))

# print(f"Created booking: {booking_id}")

id_ = "AAMkAGZiYWQ2ODlkLTE2MDctNDVhNS05MzhmLTFmMWM3OWFkODdhOQBGAAAAAABymAETdP+vQKolzvpPc5DxBwCVT8W0qtWuTbTeQfVxSArfAAAAAAENAACVT8W0qtWuTbTeQfVxSArfAAAGE1poAAA="
item = account.calendar.get(
    id=id_,
)

print(item.required_attendees)
print(outlook.get_booking_owner_blocking(id_).email)

# bookings = asyncio.run(
#     outlook.get_bookings_in_period(
#         TimePeriod(
#             start=TimeStamp(start), end=TimeStamp(start + datetime.timedelta(days=60))
#         ),
#         filter_rooms=rooms,
#     )
# )

# for booking in bookings:
#     print(booking.owner.email)
