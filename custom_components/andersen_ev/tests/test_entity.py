"""Tests for the shared AndersenEvDeviceInfoMixin."""

from unittest.mock import MagicMock

from andersen_ev.entity import AndersenEvDeviceInfoMixin


class _StubEntity(AndersenEvDeviceInfoMixin):
    """Minimal stand-in exercising the mixin without a real CoordinatorEntity."""

    def __init__(self, device) -> None:
        self._device = device
        self._attr_device_info = {"model": "A2"}


def _make_device(model_name=None, last_status=None):
    device = MagicMock()
    device.model_name = model_name
    device.last_status = last_status
    return device


class TestUpdateModelFromDeviceStatus:
    """Tests for AndersenEvDeviceInfoMixin._update_model_from_device_status()."""

    def test_uses_model_name_when_present(self):
        entity = _StubEntity(_make_device(model_name="Andersen A3"))

        entity._update_model_from_device_status()

        assert entity._attr_device_info["model"] == "Andersen A3"

    def test_falls_back_to_sys_product_name(self):
        entity = _StubEntity(_make_device(last_status={"sysProductName": "Andersen A2 Pro"}))

        entity._update_model_from_device_status()

        assert entity._attr_device_info["model"] == "Andersen A2 Pro"

    def test_falls_back_to_sys_product_id(self):
        entity = _StubEntity(_make_device(last_status={"sysProductId": "A2"}))

        entity._update_model_from_device_status()

        assert entity._attr_device_info["model"] == "A2"

    def test_falls_back_to_hw_version(self):
        entity = _StubEntity(_make_device(last_status={"sysHwVersion": "1.5"}))

        entity._update_model_from_device_status()

        assert entity._attr_device_info["model"] == "A2 (HW: 1.5)"

    def test_no_status_keeps_default_model(self):
        entity = _StubEntity(_make_device(last_status=None))

        entity._update_model_from_device_status()

        assert entity._attr_device_info["model"] == "A2"
