"""Config flow for Andersen EV integration."""
import logging
import voluptuous as vol

# Import the konnect module from the local directory
from .konnect.client import KonnectClient

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Validate the credentials by attempting to sign in
    try:
        client = KonnectClient(data[CONF_EMAIL], data[CONF_PASSWORD])
        await client.authenticate_user()
        devices = await client.getDevices()
        
        if not devices:
            raise CannotConnect("No Andersen EV devices found")
        
        # Return info to be stored in the config entry
        return {"title": f"Andersen EV ({data[CONF_EMAIL]})"}
    except Exception as e:
        _LOGGER.error("Authentication error: %s", str(e))
        if "Incorrect email address" in str(e) or "Failed to sign in" in str(e):
            raise InvalidAuth from e
        raise CannotConnect from e


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Andersen EV."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""