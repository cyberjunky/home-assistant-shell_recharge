"""The Shell Recharge integration."""

from __future__ import annotations

import logging

import shellrecharge
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ShellEvApi
from .const import DOMAIN
from .coordinator import (
    ShellRechargePublicDataUpdateCoordinator,
    ShellRechargeUserDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating configuration from version %s", entry.version)

    if entry.version == 2:
        new_data = dict(entry.data)
        new_data["public"] = {"serial_number": new_data.pop("serial_number")}
        hass.config_entries.async_update_entry(entry, data=new_data, version=3)

    if entry.version == 3:
        # v3 public entries lack client_id/client_secret; keep data as-is.
        # The coordinator will raise UpdateFailed with a helpful message when
        # credentials are missing so the user knows to reconfigure.
        hass.config_entries.async_update_entry(entry, version=4)

    _LOGGER.debug("Migration to configuration version %s successful", entry.version)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up shell_recharge_ev from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    coordinator: ShellRechargePublicDataUpdateCoordinator | ShellRechargeUserDataUpdateCoordinator

    pub = entry.data.get("public") or {}
    if pub.get("serial_number"):
        api = ShellEvApi(
            websession=async_get_clientsession(hass),
            client_id=pub.get("client_id", ""),
            client_secret=pub.get("client_secret", ""),
        )
        coordinator = ShellRechargePublicDataUpdateCoordinator(
            hass, api, pub["serial_number"]
        )
    else:
        priv = entry.data.get("private") or {}
        shell_api = shellrecharge.Api(websession=async_get_clientsession(hass))
        coordinator = ShellRechargeUserDataUpdateCoordinator(
            hass,
            await shell_api.get_user(
                priv["email"],
                priv["password"],
                priv.get("api_key"),
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
