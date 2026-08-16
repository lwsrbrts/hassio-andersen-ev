"""Tests for the Andersen EV switch platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from andersen_ev.switch import AndersenEvScheduleSwitch, async_setup_entry


def _make_device(
    device_id="device_1",
    friendly_name="Device",
    status_available=True,
    last_status=None,
    model_name=None,
):
    """Build a mock KonnectDevice."""
    device = MagicMock()
    device.device_id = device_id
    device.friendly_name = friendly_name
    device.status_available = status_available
    device.last_status = last_status
    device.model_name = model_name
    return device


def _make_coordinator(devices=None, last_update_success=True):
    """Build a mock AndersenEvCoordinator."""
    coordinator = MagicMock()
    coordinator.data = devices or []
    coordinator.last_update_success = last_update_success
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def _make_switch(coordinator, device, index=0, schedule_name="Schedule 1"):
    switch = AndersenEvScheduleSwitch(coordinator, device, index, schedule_name)
    switch.async_write_ha_state = MagicMock()
    return switch


class TestAsyncSetupEntry:
    """Tests for async_setup_entry()."""

    @pytest.mark.asyncio
    async def test_creates_switch_per_schedule_slot_with_custom_and_default_names(self):
        device = _make_device()
        device.get_device_info = AsyncMock(
            return_value={
                "deviceInfo": {"schedule0Name": "Overnight"},
                "deviceStatus": {"scheduleSlotsArray": [{"enabled": True}, {"enabled": False}]},
            }
        )
        coordinator = _make_coordinator([device])
        entry = MagicMock()
        entry.runtime_data = coordinator
        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        entities = async_add_entities.call_args.args[0]
        assert len(entities) == 2
        assert entities[0]._schedule_name == "Overnight"
        assert entities[1]._schedule_name == "Schedule 2"

    @pytest.mark.asyncio
    async def test_missing_device_info_skips_device(self):
        device = _make_device()
        device.get_device_info = AsyncMock(return_value=None)
        coordinator = _make_coordinator([device])
        entry = MagicMock()
        entry.runtime_data = coordinator
        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        assert async_add_entities.call_args.args[0] == []

    @pytest.mark.asyncio
    async def test_missing_device_info_key_skips_device(self):
        device = _make_device()
        device.get_device_info = AsyncMock(return_value={"other": True})
        coordinator = _make_coordinator([device])
        entry = MagicMock()
        entry.runtime_data = coordinator
        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        assert async_add_entities.call_args.args[0] == []

    @pytest.mark.asyncio
    async def test_missing_device_status_skips_device(self):
        device = _make_device()
        device.get_device_info = AsyncMock(return_value={"deviceInfo": {}})
        coordinator = _make_coordinator([device])
        entry = MagicMock()
        entry.runtime_data = coordinator
        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        assert async_add_entities.call_args.args[0] == []

    @pytest.mark.asyncio
    async def test_missing_schedule_slots_array_skips_device(self):
        device = _make_device()
        device.get_device_info = AsyncMock(return_value={"deviceInfo": {}, "deviceStatus": {}})
        coordinator = _make_coordinator([device])
        entry = MagicMock()
        entry.runtime_data = coordinator
        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        assert async_add_entities.call_args.args[0] == []


class TestDynamicDevices:
    """Tests for the dynamic-devices coordinator listener registered in async_setup_entry()."""

    @pytest.mark.asyncio
    async def test_new_device_scheduled_for_addition(self):
        device_a = _make_device(device_id="device_1")
        device_a.get_device_info = AsyncMock(
            return_value={
                "deviceInfo": {},
                "deviceStatus": {"scheduleSlotsArray": [{"enabled": True}]},
            }
        )
        coordinator = _make_coordinator([device_a])
        entry = MagicMock()
        entry.runtime_data = coordinator
        async_add_entities = MagicMock()
        hass = MagicMock()

        await async_setup_entry(hass, entry, async_add_entities)

        assert async_add_entities.call_count == 1
        entry.async_on_unload.assert_called_once()
        listener = coordinator.async_add_listener.call_args.args[0]

        device_b = _make_device(device_id="device_2")
        device_b.get_device_info = AsyncMock(
            return_value={
                "deviceInfo": {},
                "deviceStatus": {"scheduleSlotsArray": [{"enabled": False}, {"enabled": True}]},
            }
        )
        coordinator.data = [device_a, device_b]

        listener()

        hass.async_create_task.assert_called_once()
        scheduled_coro = hass.async_create_task.call_args.args[0]
        await scheduled_coro

        assert async_add_entities.call_count == 2
        new_entities = async_add_entities.call_args.args[0]
        assert len(new_entities) == 2
        assert all(entity._device.device_id == "device_2" for entity in new_entities)

    @pytest.mark.asyncio
    async def test_no_new_devices_does_not_schedule_a_task(self):
        device_a = _make_device(device_id="device_1")
        device_a.get_device_info = AsyncMock(
            return_value={
                "deviceInfo": {},
                "deviceStatus": {"scheduleSlotsArray": [{"enabled": True}]},
            }
        )
        coordinator = _make_coordinator([device_a])
        entry = MagicMock()
        entry.runtime_data = coordinator
        async_add_entities = MagicMock()
        hass = MagicMock()

        await async_setup_entry(hass, entry, async_add_entities)
        listener = coordinator.async_add_listener.call_args.args[0]

        listener()

        hass.async_create_task.assert_not_called()
        assert async_add_entities.call_count == 1


class TestInit:
    """Tests for AndersenEvScheduleSwitch.__init__()."""

    def test_sets_unique_id_name_icon_and_device_info(self):
        device = _make_device(device_id="device_1", friendly_name="My Charger")
        coordinator = _make_coordinator([device])

        switch = _make_switch(coordinator, device, index=2, schedule_name="Weekend")

        assert switch._attr_unique_id == "device_1_schedule_2"
        assert switch._attr_name == "Schedule 3"
        assert switch._attr_icon == "mdi:calendar-clock"
        assert switch._attr_device_info["name"] == "My Charger (device_1)"
        assert switch._attr_has_entity_name is True

    def test_extra_state_attributes(self):
        device = _make_device()
        coordinator = _make_coordinator([device])

        switch = _make_switch(coordinator, device, index=1, schedule_name="Weekend")

        assert switch.extra_state_attributes == {
            "schedule_name": "Weekend",
            "schedule_index": 1,
        }


class TestUpdateModelFromDeviceStatus:
    """Tests for AndersenEvScheduleSwitch._update_model_from_device_status()."""

    def test_uses_model_name_when_present(self):
        device = _make_device(model_name="Andersen A3")
        coordinator = _make_coordinator([device])

        switch = _make_switch(coordinator, device)

        assert switch._attr_device_info["model"] == "Andersen A3"

    def test_falls_back_to_sys_product_name(self):
        device = _make_device(last_status={"sysProductName": "Andersen A2 Pro"})
        coordinator = _make_coordinator([device])

        switch = _make_switch(coordinator, device)

        assert switch._attr_device_info["model"] == "Andersen A2 Pro"

    def test_falls_back_to_sys_product_id(self):
        device = _make_device(last_status={"sysProductId": "A2"})
        coordinator = _make_coordinator([device])

        switch = _make_switch(coordinator, device)

        assert switch._attr_device_info["model"] == "A2"

    def test_falls_back_to_hw_version(self):
        device = _make_device(last_status={"sysHwVersion": "1.5"})
        coordinator = _make_coordinator([device])

        switch = _make_switch(coordinator, device)

        assert switch._attr_device_info["model"] == "A2 (HW: 1.5)"

    def test_no_status_keeps_default_model(self):
        device = _make_device(last_status=None)
        coordinator = _make_coordinator([device])

        switch = _make_switch(coordinator, device)

        assert switch._attr_device_info["model"] == "A2"


class TestAvailable:
    """Tests for AndersenEvScheduleSwitch.available."""

    def test_available_when_device_found_and_status_available(self):
        device = _make_device(status_available=True)
        coordinator = _make_coordinator([device], last_update_success=True)
        switch = _make_switch(coordinator, device)

        assert switch.available is True

    def test_unavailable_when_status_unavailable(self):
        device = _make_device(status_available=False)
        coordinator = _make_coordinator([device], last_update_success=True)
        switch = _make_switch(coordinator, device)

        assert switch.available is False

    def test_unavailable_when_device_not_found(self):
        device = _make_device(device_id="device_1")
        coordinator = _make_coordinator([], last_update_success=True)
        switch = _make_switch(coordinator, device)

        assert switch.available is False


class TestIsOn:
    """Tests for AndersenEvScheduleSwitch.is_on."""

    def test_returns_enabled_from_schedule_slots_array(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": True}]})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)

        assert switch.is_on is True

    def test_returns_disabled_from_schedule_slots_array(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": False}]})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)

        assert switch.is_on is False

    def test_no_last_status_defaults_false(self):
        device = _make_device(last_status=None)
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)

        assert switch.is_on is False

    def test_index_out_of_range_defaults_false(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": True}]})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=5)

        assert switch.is_on is False


class TestAsyncTurnOnOff:
    """Tests for AndersenEvScheduleSwitch.async_turn_on() / async_turn_off()."""

    @pytest.mark.asyncio
    async def test_turn_on_calls_set_schedule_enabled_true(self):
        device = _make_device()
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device)
        switch._set_schedule_enabled = AsyncMock()

        await switch.async_turn_on()

        switch._set_schedule_enabled.assert_awaited_once_with(True)

    @pytest.mark.asyncio
    async def test_turn_off_calls_set_schedule_enabled_false(self):
        device = _make_device()
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device)
        switch._set_schedule_enabled = AsyncMock()

        await switch.async_turn_off()

        switch._set_schedule_enabled.assert_awaited_once_with(False)


class TestSetScheduleEnabled:
    """Tests for AndersenEvScheduleSwitch._set_schedule_enabled()."""

    @pytest.mark.asyncio
    async def test_success_with_existing_status_updates_state_and_refreshes(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": False}]})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)
        switch._send_set_schedules_mutation = AsyncMock(return_value=True)

        await switch._set_schedule_enabled(True)

        switch._send_set_schedules_mutation.assert_awaited_once()
        formatted_slots = switch._send_set_schedules_mutation.call_args.args[0]
        assert formatted_slots == {"sch0": {"enabled": True}}
        assert device.last_status["scheduleSlotsArray"][0]["enabled"] is True
        switch.async_write_ha_state.assert_called_once()
        coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_existing_status_fetches_from_api(self):
        device = _make_device(last_status=None)
        device.get_device_info = AsyncMock(return_value={"deviceStatus": {"scheduleSlotsArray": [{"enabled": False}]}})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)
        switch._send_set_schedules_mutation = AsyncMock(return_value=True)

        await switch._set_schedule_enabled(True)

        device.get_device_info.assert_awaited_once()
        switch._send_set_schedules_mutation.assert_awaited_once()
        coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_api_fetch_missing_schedule_data_raises(self):
        device = _make_device(last_status=None)
        device.get_device_info = AsyncMock(return_value={"deviceStatus": {}})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)

        with pytest.raises(HomeAssistantError):
            await switch._set_schedule_enabled(True)

    @pytest.mark.asyncio
    async def test_index_out_of_range_raises(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": False}]})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=5)

        with pytest.raises(HomeAssistantError):
            await switch._set_schedule_enabled(True)

        coordinator.async_request_refresh.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_mutation_failure_raises(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": False}]})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)
        switch._send_set_schedules_mutation = AsyncMock(return_value=False)

        with pytest.raises(HomeAssistantError):
            await switch._set_schedule_enabled(True)

        coordinator.async_request_refresh.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_success_adds_schedule_slots_array_when_removed_concurrently(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": False}], "online": True})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)

        async def mutate_and_succeed(*_args, **_kwargs):
            del device.last_status["scheduleSlotsArray"]
            return True

        switch._send_set_schedules_mutation = AsyncMock(side_effect=mutate_and_succeed)

        await switch._set_schedule_enabled(True)

        assert device.last_status["scheduleSlotsArray"][0]["enabled"] is True
        coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_success_extends_schedule_slots_array_when_shortened_concurrently(self):
        device = _make_device(last_status={"scheduleSlotsArray": [{"enabled": False}]})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)

        async def mutate_and_succeed(*_args, **_kwargs):
            device.last_status["scheduleSlotsArray"] = []
            return True

        switch._send_set_schedules_mutation = AsyncMock(side_effect=mutate_and_succeed)

        await switch._set_schedule_enabled(True)

        assert device.last_status["scheduleSlotsArray"][0]["enabled"] is True
        coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_formatted_slots_are_deep_copied_from_source(self):
        captured = {}

        async def capture_mutation(slots, *_args, **_kwargs):
            captured["slots"] = slots
            return True

        original_slots = [{"enabled": False, "start": "08:00"}]
        device = _make_device(last_status={"scheduleSlotsArray": original_slots})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device, index=0)
        switch._send_set_schedules_mutation = AsyncMock(side_effect=capture_mutation)

        await switch._set_schedule_enabled(True)

        captured["slots"]["sch0"]["start"] = "99:99"
        assert original_slots[0]["start"] == "08:00"


class TestSendSetSchedulesMutation:
    """Tests for AndersenEvScheduleSwitch._send_set_schedules_mutation()."""

    @pytest.mark.asyncio
    async def test_success_returns_true(self):
        device = _make_device()
        device.graphql_client.execute_mutation = AsyncMock(return_value={"return_value": True})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device)

        result = await switch._send_set_schedules_mutation({"sch0": {"enabled": True}}, enabled=True)

        assert result is True
        device.graphql_client.execute_mutation.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disabled_state_text(self):
        device = _make_device()
        device.graphql_client.execute_mutation = AsyncMock(return_value={"return_value": True})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device)

        result = await switch._send_set_schedules_mutation({"sch0": {"enabled": False}}, enabled=False)

        assert result is True

    @pytest.mark.asyncio
    async def test_updated_state_text_when_enabled_is_none(self):
        device = _make_device()
        device.graphql_client.execute_mutation = AsyncMock(return_value={"return_value": True})
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device)

        result = await switch._send_set_schedules_mutation({"sch0": {}}, enabled=None)

        assert result is True

    @pytest.mark.asyncio
    async def test_none_result_returns_false(self):
        device = _make_device()
        device.graphql_client.execute_mutation = AsyncMock(return_value=None)
        coordinator = _make_coordinator([device])
        switch = _make_switch(coordinator, device)

        result = await switch._send_set_schedules_mutation({"sch0": {"enabled": True}}, enabled=True)

        assert result is False
