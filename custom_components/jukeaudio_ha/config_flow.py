"""Config flow for Juke Audio integration."""
from __future__ import annotations

import ipaddress
import re

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD,CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, LOGGER
from .hub import JukeAudioHub
from jukeaudio.exceptions import AuthenticationException, UnexpectedException

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="juke.local"): str,
        vol.Required(CONF_USERNAME, default="Admin"): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_SCAN_INTERVAL, default=30): int
    }
)


def host_valid(host):
    """Return True if hostname or IP address is valid."""
    try:
        if ipaddress.ip_address(host).version == (4 or 6):
            return True
    except ValueError:
        disallowed = re.compile(r"[^a-zA-Z\d\-]")
        return all(x and not disallowed.search(x) for x in host.split("."))


async def validate_input(hass: HomeAssistant, data: dict[str, Any]):
    """Validate the user input allows us to connect."""

    if not host_valid(data[CONF_HOST]):
        raise CannotConnect
    
    if CONF_SCAN_INTERVAL in data:
        try:
            update_interval = int(data[CONF_SCAN_INTERVAL])
        except ValueError:
            raise InvalidUpdateInterval(ValueError)

    hub = JukeAudioHub(hass, data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])

    if not await hub.verify_connection():
        raise CannotConnect

    LOGGER.debug("Successfully reached the Juke amplifier on the network")
    return await hub.get_devices()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Juke Audio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                LOGGER.exception("Failed to reach Juke amplifier on the network")
                errors["base"] = "cannot_connect"
            except UnexpectedException:
                LOGGER.exception("Unknown exception")
                errors["base"] = "unknown"
            except AuthenticationException:
                LOGGER.exception("Failed to authenticate")
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                LOGGER.debug("Juke devices: %s. Registering with %s", info, info[0])
                return self.async_create_entry(title=info[0], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, user_input: dict[str, Any]) -> FlowResult:
        """Perform reauth upon an authentication error."""
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        hub: JukeAudioHub = self.hass.data[DOMAIN][self.reauth_entry.entry_id]["hub"]
        
        await hub.get_connection_info()
        LOGGER.debug("Successfully connected to the Juke amplifier")

        self.hass.config_entries.async_update_entry(self.reauth_entry, data=user_input)
        await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)

        return self.async_abort(reason="reauth_successful")


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidUpdateInterval(HomeAssistantError):
    """Error to indicate incorrect update interval setting"""