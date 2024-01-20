"""Config flow for shell_recharge_ev integration."""
from __future__ import annotations

import re
from asyncio import CancelledError
from typing import Any

import shellrechargeev
import voluptuous as vol
from aiohttp.client_exceptions import ClientError
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

RECHARGE_SCHEMA = vol.Schema({vol.Required("location_id"): str})


class ShellRechargeEVFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[misc, call-arg]
    """Handle a config flow for shell_recharge_ev."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=RECHARGE_SCHEMA)

        try:
            match = re.fullmatch(
                r"^\s*(?:[0-9]{7})\s*$",
                user_input["location_id"],
            )
            if not match:
                errors["location_id"] = "malformed_location_id"

            api = shellrechargeev.Api(websession=async_get_clientsession(self.hass))
            if not await api.location_by_id(user_input["location_id"]):
                errors["base"] = "empty_response"

        except (ClientError, TimeoutError, CancelledError):
            errors["base"] = "cannot_connect"

        if not errors:
            await self.async_set_unique_id(user_input["location_id"])
            self._abort_if_unique_id_configured(updates=user_input)
            return self.async_create_entry(
                title=f"Shell Recharge {user_input['location_id']}", data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
        )
