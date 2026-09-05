"""Shared entity helpers for Andersen EV."""

from __future__ import annotations


class AndersenEvDeviceInfoMixin:
    """Mixin providing shared device-info update logic for Andersen EV entities.

    Entities using this mixin must set ``self._device`` (a ``KonnectDevice``) and
    ``self._attr_device_info`` (a ``DeviceInfo``) before calling
    ``_update_model_from_device_status``.
    """

    def _update_model_from_device_status(self) -> None:
        """Update model information from device status if available."""
        # First try to use the model name from the API if available
        if hasattr(self._device, "model_name") and self._device.model_name:
            self._attr_device_info["model"] = self._device.model_name
        # Fall back to the information from device status
        elif self._device.last_status:
            status = self._device.last_status
            if "sysProductName" in status:
                self._attr_device_info["model"] = status["sysProductName"]
            elif "sysProductId" in status:
                self._attr_device_info["model"] = status["sysProductId"]
            elif "sysHwVersion" in status:
                self._attr_device_info["model"] = f"A2 (HW: {status['sysHwVersion']})"
