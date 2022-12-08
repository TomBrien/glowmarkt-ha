"""Access data from smart meters via Glowmarkt."""

import httpx

from . import __version__ as VERSION
from .const import (
    API_CONSUMPTION,
    API_PASSWORD,
    API_RESOURCE_ID,
    API_USERNAME,
    APPLICATION_ID,
    BASE_URL,
    ENDPOINT_AUTH,
    ENDPOINT_RESOURCE,
    Sources,
    Utilities,
)


class Utility:
    """Class to represent a utility (gas/electricity)."""

    def __init__(self, id: str, type: Utilities, source: Sources) -> None:
        """Initialise Utility object."""
        self.id = id
        self.type = type
        self.source = source


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
                            utility[API_RESOURCE_ID],
                            Utilities.ELECTRICITY
                            if Utilities.ELECTRICITY.value in utility["name"]
                            else Utilities.GAS,
                            Sources.SMART_METER
                            if Sources.SMART_METER.value in utility["name"]
                            else Sources.DCC,
                        )
                    )
            return utilities
