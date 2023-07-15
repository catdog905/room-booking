import exchangelib

from ...config import bookable_rooms
from ...config import config
from ...adapters.outlook import OutlookBookings, RoomsRegistry

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