"""Config flow for shell_recharge integration."""

from __future__ import annotations

from asyncio import CancelledError
from typing import Any

import shellrecharge
import voluptuous as vol
from aiohttp.client_exceptions import ClientError
from homeassistant import config_entries
from homeassistant.data_entry_flow import section
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from shellrecharge import LocationEmptyError, LocationValidationError
from shellrecharge.user import LoginFailedError

from .const import DOMAIN

RECHARGE_SCHEMA = vol.Schema(
    {
        vol.Optional("public"): section(
            vol.Schema(
                {
                    vol.Optional("serial_number"): str,
                }
            ),
            {"collapsed": True},
        ),
        vol.Optional("private"): section(
            vol.Schema(
                {
                    vol.Optional("email"): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.EMAIL)
                    ),
                    vol.Optional("password"): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            {"collapsed": True},
        ),
    }
)


class ShellRechargeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for shell_recharge_ev."""

    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=RECHARGE_SCHEMA)

        try:
            if user_input.get("public") and user_input["public"].get("serial_number"):
                unique_id = user_input["public"]["serial_number"]
                api = shellrecharge.Api(websession=async_get_clientsession(self.hass))
                await api.location_by_id(unique_id)
            elif (
                user_input.get("private")
                and user_input["private"].get("email")
                and user_input["private"].get("password")
            ):
                unique_id = user_input["private"]["email"]
                api = shellrecharge.Api(websession=async_get_clientsession(self.hass))
                user = await api.get_user(
                    email=unique_id,
                    pwd=user_input["private"]["password"],
                )
                user_input["private"]["api_key"] = user.cookies["tnm_api"]
            else:
                errors["base"] = "missing_data"
                return self.async_show_form(
                    step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
                )
        except LoginFailedError:
            errors["base"] = "login_failed"
        except LocationEmptyError:
            errors["base"] = "empty_response"
        except LocationValidationError:
            errors["base"] = "validation"
        except (ClientError, TimeoutError, CancelledError):
            errors["base"] = "cannot_connect"

        if not errors:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured(updates=user_input)
            return self.async_create_entry(
                title=f"Shell Recharge Charge Point ID {unique_id}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
        )
