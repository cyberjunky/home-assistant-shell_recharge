"""Shell Recharge data update coordinators."""

import logging
from asyncio.exceptions import CancelledError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from shellrecharge import Api, Location, LocationEmptyError
from shellrecharge.user import AssetsEmptyError, DetailedChargePointEmptyError, User
from shellrecharge.usermodels import DetailedAssets

from .const import DOMAIN, UPDATE_INTERVAL, SerialNumber

_LOGGER = logging.getLogger(__name__)


class ShellRechargeUserDataUpdateCoordinator(DataUpdateCoordinator):
    """Handles data updates for private chargers."""

    def __init__(self, hass: HomeAssistant, api: User) -> None:
        """Initialize coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

        self.api = api

    async def _async_update_data(self) -> DetailedAssets:
        """Fetch data from API endpoint.

        Fetches charge point information to cache for entities.
        """
        data = None
        try:
            data = await self.api.get_detailed_assets()
        except AssetsEmptyError as exc:
            _LOGGER.info("User has no charger(s) or card(s)")
            raise UpdateFailed() from exc
        except DetailedChargePointEmptyError as exc:
            _LOGGER.info("User has no charger(s)")
            raise UpdateFailed() from exc
        except CancelledError as exc:
            _LOGGER.error(
                "CancelledError occurred while fetching user's for charger(s)"
            )
            raise UpdateFailed() from exc
        except TimeoutError as exc:
            _LOGGER.error("TimeoutError occurred while fetching user's for charger(s)")
            raise UpdateFailed() from exc

        return data

    async def toggle_session(
        self, charge_point: str, charge_token: str, toggle: str
    ) -> bool:
        """Toggle a charger session."""
        return bool(
            await self.api.toggle_charger(
                charger_id=charge_point, card_rfid=charge_token, action=toggle
            )
        )


class ShellRechargePublicDataUpdateCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self, hass: HomeAssistant, api: Api, serial_number: SerialNumber
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.serial_number = serial_number

    async def _async_update_data(self) -> Location:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        data = None
        try:
            data = await self.api.location_by_id(self.serial_number)
        except LocationEmptyError as exc:
            _LOGGER.error(
                "Error occurred while fetching data for charger(s) %s, not found, or serial is invalid",
                self.serial_number,
            )
            raise UpdateFailed() from exc
        except CancelledError as exc:
            _LOGGER.error(
                "CancelledError occurred while fetching data for charger(s) %s",
                self.serial_number,
            )
            raise UpdateFailed() from exc
        except TimeoutError as exc:
            _LOGGER.error(
                "TimeoutError occurred while fetching data for charger(s) %s",
                self.serial_number,
            )
            raise UpdateFailed() from exc

        return data
