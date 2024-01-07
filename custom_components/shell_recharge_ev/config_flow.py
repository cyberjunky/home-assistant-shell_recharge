"""Config flow for shell_recharge_ev integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import shellrechargeev
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("location_id"): str,
    }
)


def verify_location_id(value: str) -> str:
    """Verify location_id is syntactically correct."""
    match = re.fullmatch(
        r"^\s*(?:[0-9]{7})\s*$", value,
    )
    if match is None:
        raise vol.Invalid(message="malformed location-id")
    return value


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        verify_location_id(data["location_id"])
    except vol.Invalid as exc:
        raise MalformedLocationId() from exc

    api = shellrechargeev.Api(websession=async_get_clientsession(hass))
    try:
        location = await api.location_by_id(data["location_id"])
    except Exception as exc:
        _LOGGER.exception(f"validate_info failed: {exc}", exc)
        raise CannotConnect(exc) from exc

    if not location:
        raise EmptyResponse()

    if location.uid != data["location_id"]:
        data["location_id"] = location.uid

    return data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for shell_recharge_ev."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}
        if await self.is_duplicate(user_input):
            return self.async_abort(reason="already_configured")
        try:
            user_input = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except MalformedLocationId:
            errors["location_id"] = "malformed_location_id"
        except EmptyResponse:
            errors["base"] = "empty_response"
        except FoundDifferentLocationId as instead:
            errors["base"] = "found_different_location"
            user_input["location_id"] = instead.instead
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            if await self.is_duplicate(user_input):
                return self.async_abort(reason="already_configured")
            return self.async_create_entry(title=user_input["location_id"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def is_duplicate(self, user_input) -> bool:
        """Check if current device is already configured."""
        for other_location in self._async_current_entries():
            if other_location.data["location_id"] == user_input["location_id"]:
                return True
        return False


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class EmptyResponse(HomeAssistantError):
    """Error to indicate we didn't find the location."""


class MalformedLocationId(HomeAssistantError):
    """Error to indicate a syntactically wrong location-id."""


class FoundDifferentLocationId(HomeAssistantError):
    """Error to indicate a found a wrong location-id."""
