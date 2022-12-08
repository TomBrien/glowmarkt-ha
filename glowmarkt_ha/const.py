"""Constants used for communication with the Glowmarkt API."""

from enum import Enum

# This is a publicly available ID, it is not a secret.
APPLICATION_ID = "b0f1b774-a586-4f72-9edd-27ead8aa7a8d"
BASE_URL = "https://api.glowmarkt.com/api/v0-1/"

API_PASSWORD = "password"
API_USERNAME = "username"

API_CONSUMPTION = "consumption"
API_RESOURCE_ID = "resourceId"
API_RESOURCE_NAME = "name"

ENDPOINT_AUTH = "auth"
ENDPOINT_RESOURCE = "resource"


class Utilities(Enum):
    """Enum for utility types."""

    GAS = "gas"
    ELECTRICITY = "electricity"


class Sources(Enum):
    """Enum for meter reading sources."""

    DCC = "DCC"
    SMART_METER = "smart meter"