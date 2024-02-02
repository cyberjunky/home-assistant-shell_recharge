"""Config flow for shell_recharge integration."""
from __future__ import annotations

from asyncio import CancelledError
from typing import Any

import shellrecharge
import voluptuous as vol
from aiohttp.client_exceptions import ClientError
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from shellrecharge import LocationEmptyError, LocationValidationError

from .const import DOMAIN

RECHARGE_SCHEMA = vol.Schema({vol.Required("serial_number"): str})


class ShellRechargeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[misc, call-arg]
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
            api = shellrecharge.Api(websession=async_get_clientsession(self.hass))
            await api.location_by_id(user_input["serial_number"])
        except LocationEmptyError:
            errors["base"] = "empty_response"
        except LocationValidationError:
            errors["base"] = "validation"
        except (ClientError, TimeoutError, CancelledError):
            errors["base"] = "cannot_connect"

        if not errors:
            await self.async_set_unique_id(user_input["serial_number"])
            self._abort_if_unique_id_configured(updates=user_input)
            return self.async_create_entry(
                title=f"Shell Recharge Charge Point ID {user_input['serial_number']}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
        )
