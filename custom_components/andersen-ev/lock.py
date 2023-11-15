"""Platform for light integration."""
from __future__ import annotations

import logging

from andersen_ev import AndersenA2
import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.lock import (PLATFORM_SCHEMA, LockEntity)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    username = config[CONF_USERNAME]
    password = config.get(CONF_PASSWORD)

    # Setup connection with devices/cloud
    a2 = AndersenA2()
    a2.authenticate(username, password)

    # Verify that passed in configuration works
    #if not a2.confirm_device(CONF_DEVICE):
    #    _LOGGER.error("Could not connect to AwesomeLight hub")
    #    return

    # Add devices
    #devices = a2.get_current_user_devices()
    
    #add_entities(AwesomeLight(light) for light in hub.lights())
    #add_entities(AndersenA2Device(user_device) for user_device in devices)
    
    #device = a2.get_device(devices['getCurrentUserDevices'][0]['id'])
    
    add_entities(AndersenA2Device(a2))


class AndersenA2Device(LockEntity):
    """Representation of an Andersen A2."""

    def __init__(self, lock) -> None:
        """Initialize an Andersen A2."""
        self._id = lock['id']
        self._name = lock['name']
        self._state = None
        

    @property
    def name(self) -> str:
        """Return the display name of this lock."""
        return self._name

    @property
    def is_locked(self) -> bool | None:
        """Return true if Andersen is locked."""
        return self._state

    def lock(self, **kwargs: Any) -> None:
        """Instruct the light to turn on. """
        self._lock

    def unlock(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._light.turn_off()

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._light.update()
        self._state = self._light.is_on()
        self._brightness = self._light.brightness