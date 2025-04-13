"""The shell_recharge integration."""

from __future__ import annotations

import logging

import shellrecharge
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import (
    ShellRechargePublicDataUpdateCoordinator,
    ShellRechargeUserDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating configuration from %s", entry.version)

    if entry.version == 2:
        new_data = {**entry.data}
        new_data["public"]["serial_number"] = new_data["serial_number"]
        del new_data["serial_number"]

    hass.config_entries.async_update_entry(entry, data=new_data, version=3)

    _LOGGER.debug("Migration to configuration version %s successful", entry.version)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up shell_recharge_ev from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    api = shellrecharge.Api(websession=async_get_clientsession(hass))

    if entry.data.get("public") and entry.data["public"].get("serial_number"):
        coordinator = ShellRechargePublicDataUpdateCoordinator(
            hass, api, entry.data["public"]["serial_number"]
        )
    else:
        coordinator = ShellRechargeUserDataUpdateCoordinator(
            hass,
            await api.get_user(
                entry.data["private"]["email"],
                entry.data["private"]["password"],
                entry.data["private"].get("api_key"),
            ),
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
