"""Access data from smart meters via Glowmarkt."""

import datetime
from dataclasses import dataclass

import httpx

from . import __version__ as VERSION
from .const import (
    API_CONSUMPTION,
    API_PASSWORD,
    API_RESOURCE_ID,
    API_RESPONSE_DATA,
    API_RESPONSE_RATE,
    API_RESPONSE_STANDING_CHARGE,
    API_RESPONSE_UNIT,
    API_USERNAME,
    APPLICATION_ID,
    BASE_URL,
    ENDPOINT_AUTH,
    ENDPOINT_READMETER,
    ENDPOINT_RESOURCE,
    ENDPOINT_TARIFF,
    Sources,
    Utilities,
)


@dataclass
class Reading:
    """Class to represent a meter reading"""

    def __init__(
        self,
        resource_id: str,
        utility_type: Utilities,
        source: Sources,
        response: dict,
    ) -> None:
        """Initialise Reading object."""
        self.resource_id = resource_id
        self.utility_type = utility_type
        self.source = source
        self._raw_response = response
        self._json = response.json()
        self.timestamp = datetime.datetime.fromtimestamp(
            self._json[API_RESPONSE_DATA][-1][0]
        )
        self.value = self._json[API_RESPONSE_DATA][-1][1]
        self.unit = self._json[API_RESPONSE_UNIT]


class Utility:
    """Class to represent a utility (gas/electricity)."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        resource_id: str,
        utility_type: Utilities,
        source: Sources,
    ) -> None:
        """Initialise Utility object."""
        self._client = client
        self.resource_id = resource_id
        self.utility_type = utility_type
        self.source = source

    async def read_meter(self) -> float:
        """Read current meter value."""
        response = await self._client.get(
            BASE_URL + ENDPOINT_RESOURCE + self.resource_id + "/" + ENDPOINT_READMETER
        )
        if response.status_code == 200:
            return Reading(self.resource_id, self.utility_type, self.source, response)

    async def get_tariff(self) -> dict:
        """Get current tariff."""
        response = await self._client.get(
            BASE_URL + ENDPOINT_RESOURCE + self.resource_id + "/" + ENDPOINT_TARIFF
        )
        if response.status_code == 200:
            return {
                "rate": response.json()[API_RESPONSE_RATE],
                "standing": response.json()[API_RESPONSE_STANDING_CHARGE],
            }

    def update_client(self, client: httpx.AsyncClient) -> None:
        """Update client."""
        self._client = client


class House:
    """Representation of a house's smart meters."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        """Initialise House object."""
        if not client:
            client = httpx.AsyncClient()
            client.headers.update({"user-agent": f"Glowmarkt-HA-{VERSION}"})

        client.headers.update(
            {"applicationID": APPLICATION_ID, "Content-Type": "application/json"}
        )

        self._client = client
        self._token: str | None = None

    async def auth(self, username: str, password: str) -> bool:
        """Authenticate with Glowmarkt."""
        if self._token:
            self._client.headers.update({"token": self._token})
            response = await self._client.get(BASE_URL + ENDPOINT_AUTH)
            if response.status_code == 200:
                return True
            self._token = None
        response = await self._client.post(
            BASE_URL + ENDPOINT_AUTH,
            json={API_USERNAME: username, API_PASSWORD: password},
        )
        if response.status_code == 200:
            self._token = response.json()["token"]
            self._client.headers.update({"token": self._token})
            return True
        return False

    async def get_utilities(self) -> list[Utility]:
        """Get and sort all utilities connected to account."""
        response = await self._client.get(BASE_URL + ENDPOINT_RESOURCE)
        if response.status_code == 200:
            utilities = []
            for utility in response.json():
                if API_CONSUMPTION in utility["name"]:
                    utilities.append(
                        Utility(
                            self._client,
                            utility[API_RESOURCE_ID],
                            Utilities.ELECTRICITY
                            if Utilities.ELECTRICITY.value in utility["name"].lower()
                            else Utilities.GAS,
                            Sources.SMART_METER
                            if Sources.SMART_METER.value in utility["name"].lower()
                            else Sources.DCC,
                        )
                    )
            return utilities
