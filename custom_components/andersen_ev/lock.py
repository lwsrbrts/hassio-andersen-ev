"""Support for Andersen EV locks."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AndersenEvCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Andersen EV lock platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for device in coordinator.data:
        entities.append(AndersenEvLock(coordinator, device))
    
    async_add_entities(entities)


class AndersenEvLock(CoordinatorEntity, LockEntity):
    """Representation of an Andersen EV charging lock."""

    def __init__(self, coordinator: AndersenEvCoordinator, device) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{device.device_id}_lock"
        self._attr_name = f"{device.friendly_name} Lock"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=f"{device.friendly_name} ({device.device_id})",
            manufacturer="Andersen EV",
            model="A2",  # Default model, will be updated if available from device status
            serial_number=f"{device.device_id}"
        )
        # Update model if device status is already available
        self._update_model_from_device_status()

    def _update_model_from_device_status(self):
        """Update model information from device status if available."""
        if hasattr(self._device, '_last_status') and self._device._last_status:
            status = self._device._last_status
            if "sysProductName" in status:
                self._attr_device_info["model"] = status["sysProductName"]
            elif "sysProductId" in status:
                self._attr_device_info["model"] = status["sysProductId"]
            elif "sysHwVersion" in status:
                self._attr_device_info["model"] = f"A2 (HW: {status['sysHwVersion']})"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        for device in self.coordinator.data:
            if device.device_id == self._device.device_id:
                self._device = device
                # Try to update model info if we have device status
                self._update_model_from_device_status()
                return True
        
        # Device no longer exists
        return False

    @property
    def is_locked(self) -> bool:
        """Return true if the lock is locked (charging disabled)."""
        for device in self.coordinator.data:
            if device.device_id == self._device.device_id:
                self._device = device
                
                # Get most recent device status from coordinator data
                for device in self.coordinator.data:
                    if device.device_id == self._device.device_id:
                        try:
                            # We'll check the last known state from coordinator
                            # This works because the coordinator refreshes regularly
                            # and we also refresh after lock/unlock actions
                            if hasattr(device, '_last_status') and device._last_status:
                                if 'sysUserLock' in device._last_status:
                                    _LOGGER.debug(f"Device {device.friendly_name} sysUserLock state: {device._last_status['sysUserLock']}")
                                    return device._last_status['sysUserLock']
                        except Exception as err:
                            _LOGGER.error(f"Error getting lock state: {err}")
                
                # Fallback to the device's user_lock property
                return not device.user_lock  # Inverted because enabled=unlocked, disabled=locked
        
        # Device no longer exists
        return False

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the charging station (disable charging)."""
        await self._device.disable()
        _LOGGER.debug(f"Locking device {self._device.friendly_name} (disabling charging)")
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the charging station (enable charging)."""
        await self._device.enable()
        _LOGGER.debug(f"Unlocking device {self._device.friendly_name} (enabling charging)")
        await self.coordinator.async_request_refresh()