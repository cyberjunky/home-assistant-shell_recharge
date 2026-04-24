"""Config flow for Shell Recharge integration."""

from __future__ import annotations

from asyncio import CancelledError
from typing import Any

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
from shellrecharge.user import LoginFailedError

from .api import ShellEvApi, ShellEvAuthError, ShellEvLocationNotFoundError
from .const import DOMAIN

import shellrecharge

RECHARGE_SCHEMA = vol.Schema(
    {
        vol.Optional("public"): section(
            vol.Schema(
                {
                    vol.Optional("serial_number"): str,
                    vol.Optional("client_id"): str,
                    vol.Optional("client_secret"): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
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

    VERSION = 4

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=RECHARGE_SCHEMA)

        try:
            pub = user_input.get("public") or {}
            priv = user_input.get("private") or {}

            if pub.get("serial_number") and pub.get("client_id") and pub.get("client_secret"):
                unique_id = pub["serial_number"]
                api = ShellEvApi(
                    websession=async_get_clientsession(self.hass),
                    client_id=pub["client_id"],
                    client_secret=pub["client_secret"],
                )
                await api.location_by_id(unique_id)

            elif priv.get("email") and priv.get("password"):
                unique_id = priv["email"]
                shell_api = shellrecharge.Api(websession=async_get_clientsession(self.hass))
                user = await shell_api.get_user(
                    email=unique_id,
                    pwd=priv["password"],
                )
                user_input["private"]["api_key"] = user.cookies["tnm_api"]

            else:
                errors["base"] = "missing_data"
                return self.async_show_form(
                    step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
                )

        except LoginFailedError:
            errors["base"] = "login_failed"
        except ShellEvAuthError:
            errors["base"] = "auth_failed"
        except ShellEvLocationNotFoundError:
            errors["base"] = "empty_response"
        except (ClientError, TimeoutError, CancelledError):
            errors["base"] = "cannot_connect"

        if not errors:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured(updates=user_input)
            return self.async_create_entry(
                title=f"Shell Recharge {unique_id}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
        )
