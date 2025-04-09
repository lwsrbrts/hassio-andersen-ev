"""The Andersen EV Charger integration."""
import logging
import asyncio
from datetime import timedelta

import voluptuous as vol

# Import the konnect module from the local directory
from .konnect.client import KonnectClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import (
    DOMAIN, 
    DEFAULT_SCAN_INTERVAL, 
    SERVICE_ENABLE_CHARGING,
    SERVICE_DISABLE_CHARGING,
    ATTR_DEVICE_ID
)

PLATFORMS = [Platform.LOCK, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Andersen EV component."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Andersen EV from a config entry."""
    email = entry.data["email"]
    password = entry.data["password"]

    coordinator = AndersenEvCoordinator(hass, email, password)
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Register services
    async def enable_charging(call: ServiceCall) -> None:
        """Enable charging for a device."""
        device_id = call.data.get(ATTR_DEVICE_ID)
        devices = coordinator.data
        
        for device in devices:
            if device.device_id == device_id:
                await device.enable()
                await coordinator.async_request_refresh()
                break
    
    async def disable_charging(call: ServiceCall) -> None:
        """Disable charging for a device."""
        device_id = call.data.get(ATTR_DEVICE_ID)
        devices = coordinator.data
        
        for device in devices:
            if device.device_id == device_id:
                await device.disable()
                await coordinator.async_request_refresh()
                break
    
    # Register services using simpler schema
    service_schema = vol.Schema({vol.Required(ATTR_DEVICE_ID): str})
    
    hass.services.async_register(
        DOMAIN, SERVICE_ENABLE_CHARGING, enable_charging, schema=service_schema
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_DISABLE_CHARGING, disable_charging, schema=service_schema
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unload_ok

class AndersenEvCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Andersen EV."""

    def __init__(self, hass: HomeAssistant, email: str, password: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = KonnectClient(email, password)
        self.devices = []

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            # If not authenticated, authenticate
            if self.client.token is None:
                await self.client.authenticate_user()
            
            # Get devices
            devices = await self.client.getDevices()
            if not devices:
                _LOGGER.warning("No devices found")
            else:
                # For each device, fetch the current status
                for device in devices:
                    _LOGGER.debug(f"Device ID: {device.device_id}, Name: {device.friendly_name}, User Lock: {device.user_lock}")
                    
                    # Fetch and log device status
                    try:
                        device_status = await device.getDeviceStatus()
                        if device_status:
                            _LOGGER.debug(f"Device Status for {device.friendly_name}: {device_status}")
                            if 'evseState' in device_status:
                                _LOGGER.debug(f"EVSE State: {device_status['evseState']}")
                            if 'online' in device_status:
                                _LOGGER.debug(f"Online: {device_status['online']}")
                            if 'sysChargingEnabled' in device_status:
                                _LOGGER.debug(f"System Charging Enabled: {device_status['sysChargingEnabled']}")
                            if 'sysUserLock' in device_status:
                                _LOGGER.debug(f"System User Lock: {device_status['sysUserLock']}")
                    except Exception as status_err:
                        _LOGGER.debug(f"Error getting device status for {device.friendly_name}: {status_err}")
            
            return devices
        except Exception as err:
            if "Failed to sign in" in str(err):
                raise ConfigEntryAuthFailed("Authentication failed") from err
            raise UpdateFailed(f"Error communicating with Andersen EV API: {err}")