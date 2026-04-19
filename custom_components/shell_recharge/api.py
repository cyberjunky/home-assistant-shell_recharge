"""Async client for the official Shell EV API (api.shell.com/ev/v1)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError

_LOGGER = logging.getLogger(__name__)

OAUTH_URL = "https://api.shell.com/v2/oauth/token"
API_BASE = "https://api.shell.com/ev/v1"


class ShellEvApiError(Exception):
    """Base exception for Shell EV API errors."""


class ShellEvAuthError(ShellEvApiError):
    """Raised when OAuth2 authentication fails."""


class ShellEvLocationNotFoundError(ShellEvApiError):
    """Raised when a location cannot be found."""


@dataclass
class ElectricalProperties:
    """Connector electrical properties."""

    powerType: str = ""
    voltage: float = 0.0
    amperage: float = 0.0
    maxElectricPower: float = 0.0


@dataclass
class Tariff:
    """Connector tariff information."""

    startFee: float = 0.0
    perMinute: float = 0.0
    perKWh: float = 0.0
    currency: str = ""
    updated: str = ""
    updatedBy: str = ""
    structure: str = ""


@dataclass
class Connector:
    """Single connector on an EVSE."""

    uid: int = 0
    externalId: str = ""
    connectorType: str = "Unspecified"
    electricalProperties: ElectricalProperties = field(default_factory=ElectricalProperties)
    fixedCable: bool = False
    tariff: Tariff = field(default_factory=Tariff)


@dataclass
class Evse:
    """Electric Vehicle Supply Equipment unit."""

    uid: int = 0
    externalId: str = ""
    evseId: str = ""
    status: str = "Unknown"
    connectors: list[Connector] = field(default_factory=list)


@dataclass
class Coordinates:
    """Geographic coordinates."""

    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class Address:
    """Location address."""

    streetAndNumber: str = ""
    postalCode: str = ""
    city: str = ""
    country: str = ""


@dataclass
class AccessibilityV2:
    """Accessibility status."""

    status: str = ""


@dataclass
class Location:
    """Shell Recharge charging location with one or more EVSEs."""

    uid: int = 0
    externalId: str = ""
    coordinates: Coordinates = field(default_factory=Coordinates)
    operatorName: str = ""
    address: Address = field(default_factory=Address)
    evses: list[Evse] = field(default_factory=list)
    accessibilityV2: AccessibilityV2 = field(default_factory=AccessibilityV2)
    suboperatorName: str = ""
    supportPhoneNumber: str = ""
    openTwentyFourSeven: bool = True


# Status values returned by the Shell EV API
EVSE_STATUS_OPTIONS = ["Available", "Occupied", "Unavailable", "Unknown"]


class ShellEvApi:
    """Async client for the Shell EV public locations API."""

    def __init__(
        self,
        websession: ClientSession,
        client_id: str,
        client_secret: str,
    ) -> None:
        """Initialise with aiohttp session and OAuth2 credentials."""
        self._session = websession
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token: str | None = None
        self._token_expires_at: datetime = datetime.min

    async def _get_token(self) -> str:
        """Return a valid Bearer token, fetching a new one when expired."""
        if self._access_token and datetime.now() < self._token_expires_at:
            return self._access_token

        _LOGGER.debug("Fetching new Shell EV API OAuth2 token")
        try:
            async with self._session.post(
                OAUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Accept": "application/json"},
                timeout=None,
            ) as resp:
                if resp.status in (401, 403):
                    raise ShellEvAuthError(
                        "Invalid client_id or client_secret. "
                        "Register at developer.shell.com to obtain credentials."
                    )
                resp.raise_for_status()
                data = await resp.json()
        except ClientError as err:
            raise ShellEvApiError(f"Network error fetching OAuth token: {err}") from err

        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        # Refresh 60 s before expiry to avoid edge-case failures
        self._token_expires_at = datetime.now() + timedelta(seconds=max(expires_in - 60, 0))
        return self._access_token

    async def location_by_id(self, location_id: str) -> Location:
        """Return a Location by its external ID (serial number).

        Searches the /locations endpoint filtered by locationExternalId.
        """
        token = await self._get_token()
        request_id = str(uuid.uuid4())

        _LOGGER.debug("Fetching Shell EV location for external ID %s", location_id)
        try:
            async with self._session.get(
                f"{API_BASE}/locations",
                params={"locationExternalId": location_id, "perPage": 1},
                headers={
                    "Authorization": f"Bearer {token}",
                    "RequestId": request_id,
                    "Accept": "application/json",
                },
                timeout=None,
            ) as resp:
                if resp.status == 401:
                    # Token may have been revoked; clear cache and raise
                    self._access_token = None
                    raise ShellEvAuthError("Bearer token rejected by API")
                if resp.status == 404:
                    raise ShellEvLocationNotFoundError(
                        f"Location with external ID '{location_id}' not found"
                    )
                resp.raise_for_status()
                result = await resp.json()
        except ClientError as err:
            raise ShellEvApiError(f"Network error fetching location: {err}") from err

        items: list[dict] = result.get("data", [])
        if not items:
            raise ShellEvLocationNotFoundError(
                f"No location returned for external ID '{location_id}'"
            )

        return self._parse_location(items[0])

    # ------------------------------------------------------------------
    # Internal parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_connector(data: dict) -> Connector:
        ep = data.get("electricalProperties") or {}
        tariff_data = data.get("tariff") or {}
        return Connector(
            uid=data.get("uid", 0),
            externalId=data.get("externalId", ""),
            connectorType=data.get("connectorType", "Unspecified"),
            electricalProperties=ElectricalProperties(
                powerType=ep.get("powerType", ""),
                voltage=float(ep.get("voltage", 0)),
                amperage=float(ep.get("amperage", 0)),
                maxElectricPower=float(ep.get("maxElectricPower", 0)),
            ),
            fixedCable=bool(data.get("fixedCable", False)),
            tariff=Tariff(
                startFee=float(tariff_data.get("startFee", 0)),
                perMinute=float(tariff_data.get("perMinute", 0)),
                perKWh=float(tariff_data.get("perKWh", 0)),
                currency=tariff_data.get("currency", ""),
                updated=tariff_data.get("updated", ""),
                updatedBy=tariff_data.get("updatedBy", ""),
                structure=tariff_data.get("structure", ""),
            ),
        )

    def _parse_evse(self, data: dict) -> Evse:
        return Evse(
            uid=data.get("uid", 0),
            externalId=data.get("externalId", ""),
            evseId=data.get("evseId", ""),
            status=data.get("status", "Unknown"),
            connectors=[
                self._parse_connector(c) for c in (data.get("connectors") or [])
            ],
        )

    def _parse_location(self, data: dict) -> Location:
        coords = data.get("coordinates") or {}
        addr = data.get("address") or {}
        acc = data.get("accessibility") or {}
        return Location(
            uid=data.get("uid", 0),
            externalId=str(data.get("externalId", "")),
            coordinates=Coordinates(
                latitude=float(coords.get("latitude", 0)),
                longitude=float(coords.get("longitude", 0)),
            ),
            operatorName=data.get("operatorName", ""),
            address=Address(
                streetAndNumber=addr.get("streetAndNumber", ""),
                postalCode=addr.get("postalCode", ""),
                city=addr.get("city", ""),
                country=addr.get("country", ""),
            ),
            evses=[self._parse_evse(e) for e in (data.get("evses") or [])],
            accessibilityV2=AccessibilityV2(status=acc.get("status", "")),
            suboperatorName=data.get("suboperatorName", ""),
            supportPhoneNumber=data.get("supportPhoneNumber", ""),
            openTwentyFourSeven=bool(data.get("openTwentyFourSeven", True)),
        )
