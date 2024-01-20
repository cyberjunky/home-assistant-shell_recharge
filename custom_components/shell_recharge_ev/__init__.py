"""The shell_recharge_ev integration."""
from __future__ import annotations

import logging

import shellrechargeev
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, UPDATE_INTERVAL, LocationId

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up shell_recharge_ev from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    api = shellrechargeev.Api(websession=async_get_clientsession(hass))

    coordinator = ShellRechargeEVDataUpdateCoordinator(
        hass, api, entry.data["location_id"]
    )
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ShellRechargeEVDataUpdateCoordinator(DataUpdateCoordinator):  # type: ignore[misc]
    """My custom coordinator."""

    def __init__(
        self, hass: HomeAssistant, api: shellrechargeev.Api, location_id: LocationId
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.location_id = location_id

    async def _async_update_data(self) -> shellrechargeev.Location:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        return await self.api.location_by_id(self.location_id)
