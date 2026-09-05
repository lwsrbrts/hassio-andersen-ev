"""Tests for the Andersen EV config flow.

These tests only run in CI (the local .venv can't install `homeassistant`; see CLAUDE.md). They
avoid the `pytest-homeassistant-custom-component` `hass` fixture (not a project dependency) by
driving `ConfigFlow` directly and stubbing the framework hooks (`async_set_unique_id`,
`_abort_if_unique_id_configured`, `async_create_entry`, `async_show_form`) it's expected to call,
rather than exercising Home Assistant's internal flow manager.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.data_entry_flow import FlowResultType

from andersen_ev.config_flow import CannotConnect, ConfigFlow, InvalidAuth, validate_input
from andersen_ev.const import CONF_EMAIL, CONF_PASSWORD
from andersen_ev.konnect.exceptions import AndersenAuthError, AndersenConnectionError

MANIFEST_PATH = Path(__file__).parent.parent / "manifest.json"


def _make_flow():
    """Create a ConfigFlow instance with the framework hooks stubbed out.

    `ConfigFlow` is normally instantiated by Home Assistant's flow manager, which assigns
    `hass`/`flow_id` before any step runs. Direct instantiation skips that, so the methods that
    depend on it are replaced with mocks; the tests below only assert on how `async_step_user`
    calls them, not on the framework's own behavior.
    """
    flow = ConfigFlow()
    flow.hass = MagicMock()
    flow.async_set_unique_id = AsyncMock(return_value=None)
    flow._abort_if_unique_id_configured = MagicMock(return_value=None)
    flow.async_create_entry = MagicMock(side_effect=lambda **kwargs: {"type": FlowResultType.CREATE_ENTRY, **kwargs})
    flow.async_show_form = MagicMock(side_effect=lambda **kwargs: {"type": FlowResultType.FORM, **kwargs})
    return flow


def _patch_konnect_client(*, devices=None, auth_error=None):
    """Patch andersen_ev.config_flow.KonnectClient with a canned authenticate/getDevices result."""
    mock_client = MagicMock()
    if auth_error is not None:
        mock_client.authenticate_user = AsyncMock(side_effect=auth_error)
    else:
        mock_client.authenticate_user = AsyncMock()
    mock_client.getDevices = AsyncMock(return_value=devices if devices is not None else [MagicMock()])
    return patch("andersen_ev.config_flow.KonnectClient", return_value=mock_client)


class TestValidateInput:
    """Tests for the validate_input() helper, independent of the flow/hass plumbing."""

    @pytest.mark.asyncio
    async def test_success_returns_title(self):
        """validate_input() returns a title built from the email on success."""
        with _patch_konnect_client():
            result = await validate_input(None, {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "testpass"})

        assert result == {"title": "Andersen EV (test@example.com)"}

    @pytest.mark.asyncio
    async def test_sign_in_failure_raises_invalid_auth(self):
        """An AndersenAuthError from authenticate_user is mapped to InvalidAuth."""
        with _patch_konnect_client(auth_error=AndersenAuthError("Failed to sign in")):
            with pytest.raises(InvalidAuth):
                await validate_input(None, {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "wrong"})

    @pytest.mark.asyncio
    async def test_connection_failure_raises_cannot_connect(self):
        """An AndersenConnectionError is mapped to CannotConnect."""
        with _patch_konnect_client(auth_error=AndersenConnectionError("network unreachable")):
            with pytest.raises(CannotConnect):
                await validate_input(None, {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "testpass"})

    @pytest.mark.asyncio
    async def test_unexpected_failure_raises_cannot_connect(self):
        """An unrecognized (non-Andersen) error is still mapped to CannotConnect."""
        with _patch_konnect_client(auth_error=Exception("something unexpected")):
            with pytest.raises(CannotConnect):
                await validate_input(None, {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "testpass"})

    @pytest.mark.asyncio
    async def test_no_devices_raises_cannot_connect(self):
        """An account with no Andersen devices is treated as CannotConnect."""
        with _patch_konnect_client(devices=[]):
            with pytest.raises(CannotConnect):
                await validate_input(None, {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "testpass"})


class TestAsyncStepUser:
    """Tests for ConfigFlow.async_step_user()."""

    @pytest.mark.asyncio
    async def test_success_sets_unique_id_and_creates_entry(self):
        """A successful sign-in sets the unique id (lowercased email) before creating the entry."""
        flow = _make_flow()
        user_input = {CONF_EMAIL: "Test@Example.com", CONF_PASSWORD: "testpass"}

        with _patch_konnect_client():
            result = await flow.async_step_user(user_input)

        flow.async_set_unique_id.assert_awaited_once_with("test@example.com")
        flow._abort_if_unique_id_configured.assert_called_once_with()
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Andersen EV (Test@Example.com)"
        assert result["data"] == user_input

    @pytest.mark.asyncio
    async def test_duplicate_email_aborts(self):
        """A second entry for an already-configured email aborts instead of being created."""
        flow = _make_flow()
        flow._abort_if_unique_id_configured = MagicMock(side_effect=data_entry_flow.AbortFlow("already_configured"))
        user_input = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "testpass"}

        with _patch_konnect_client():
            with pytest.raises(data_entry_flow.AbortFlow) as exc_info:
                await flow.async_step_user(user_input)

        assert exc_info.value.reason == "already_configured"
        flow.async_create_entry.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_auth_shows_form_error_without_setting_unique_id(self):
        """An invalid-auth failure re-shows the form and never touches the unique id."""
        flow = _make_flow()
        user_input = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "wrong"}

        with _patch_konnect_client(auth_error=AndersenAuthError("Failed to sign in")):
            result = await flow.async_step_user(user_input)

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}
        flow.async_set_unique_id.assert_not_awaited()
        flow.async_create_entry.assert_not_called()

    @pytest.mark.asyncio
    async def test_cannot_connect_shows_form_error_without_setting_unique_id(self):
        """A connection failure re-shows the form and never touches the unique id."""
        flow = _make_flow()
        user_input = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "testpass"}

        with _patch_konnect_client(auth_error=AndersenConnectionError("boom")):
            result = await flow.async_step_user(user_input)

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
        flow.async_set_unique_id.assert_not_awaited()
        flow.async_create_entry.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_input_shows_initial_form(self):
        """Calling the step with no input just shows the empty form."""
        flow = _make_flow()

        result = await flow.async_step_user(None)

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {}
        flow.async_set_unique_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unexpected_exception_shows_unknown_error(self):
        """An exception that escapes validate_input's own handling shows the 'unknown' error."""
        flow = _make_flow()
        user_input = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "testpass"}

        with patch("andersen_ev.config_flow.validate_input", AsyncMock(side_effect=Exception("boom"))):
            result = await flow.async_step_user(user_input)

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}
        flow.async_set_unique_id.assert_not_awaited()
        flow.async_create_entry.assert_not_called()


def _make_reauth_flow(email="test@example.com", password="oldpass"):
    """Create a ConfigFlow instance stubbed for reauth-step tests.

    Builds on `_make_flow()` and additionally stubs `_get_reauth_entry` (normally supplied by
    HA's flow manager for reauth flows) and `async_update_reload_and_abort`.
    """
    flow = _make_flow()
    mock_entry = MagicMock()
    mock_entry.data = {CONF_EMAIL: email, CONF_PASSWORD: password}
    flow._get_reauth_entry = MagicMock(return_value=mock_entry)
    flow.async_update_reload_and_abort = MagicMock(
        side_effect=lambda entry, **kw: {"type": FlowResultType.ABORT, "reason": "reauth_successful"}
    )
    return flow


class TestAsyncStepReauth:
    """Tests for ConfigFlow.async_step_reauth() and async_step_reauth_confirm()."""

    @pytest.mark.asyncio
    async def test_reauth_delegates_to_confirm_step(self):
        """async_step_reauth() shows the reauth confirmation form."""
        flow = _make_reauth_flow()

        result = await flow.async_step_reauth({CONF_EMAIL: "test@example.com"})

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

    @pytest.mark.asyncio
    async def test_reauth_confirm_no_input_shows_form_with_email(self):
        """Calling reauth_confirm with no input shows the form with the stored email."""
        flow = _make_reauth_flow(email="user@example.com")

        result = await flow.async_step_reauth_confirm(None)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["description_placeholders"] == {"email": "user@example.com"}
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_reauth_confirm_success_updates_entry(self):
        """A successful reauth updates the entry password and aborts with reauth_successful."""
        flow = _make_reauth_flow(email="test@example.com", password="oldpass")

        with _patch_konnect_client():
            result = await flow.async_step_reauth_confirm({CONF_PASSWORD: "newpass"})

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        flow.async_update_reload_and_abort.assert_called_once()
        _, kwargs = flow.async_update_reload_and_abort.call_args
        assert kwargs["data_updates"] == {CONF_PASSWORD: "newpass"}

    @pytest.mark.asyncio
    async def test_reauth_confirm_invalid_auth_shows_error(self):
        """An AndersenAuthError during reauth re-shows the form with invalid_auth."""
        flow = _make_reauth_flow()

        with _patch_konnect_client(auth_error=AndersenAuthError("bad password")):
            result = await flow.async_step_reauth_confirm({CONF_PASSWORD: "wrong"})

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}
        flow.async_update_reload_and_abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_reauth_confirm_cannot_connect_shows_error(self):
        """An AndersenConnectionError during reauth re-shows the form with cannot_connect."""
        flow = _make_reauth_flow()

        with _patch_konnect_client(auth_error=AndersenConnectionError("network down")):
            result = await flow.async_step_reauth_confirm({CONF_PASSWORD: "newpass"})

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
        flow.async_update_reload_and_abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_reauth_confirm_unknown_error_shows_error(self):
        """An unexpected exception during reauth re-shows the form with unknown."""
        flow = _make_reauth_flow()

        with patch("andersen_ev.config_flow.validate_input", AsyncMock(side_effect=Exception("boom"))):
            result = await flow.async_step_reauth_confirm({CONF_PASSWORD: "newpass"})

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}
        flow.async_update_reload_and_abort.assert_not_called()


def _make_reconfigure_flow(email="test@example.com", password="oldpass"):
    """Create a ConfigFlow instance stubbed for reconfigure-step tests.

    Builds on `_make_flow()` and additionally stubs `_get_reconfigure_entry` (normally supplied by
    HA's flow manager for reconfigure flows) and `async_update_reload_and_abort`.
    """
    flow = _make_flow()
    mock_entry = MagicMock()
    mock_entry.data = {CONF_EMAIL: email, CONF_PASSWORD: password}
    flow._get_reconfigure_entry = MagicMock(return_value=mock_entry)
    flow.async_update_reload_and_abort = MagicMock(
        side_effect=lambda entry, **kw: {"type": FlowResultType.ABORT, "reason": "reconfigure_successful"}
    )
    return flow


class TestAsyncStepReconfigure:
    """Tests for ConfigFlow.async_step_reconfigure()."""

    @pytest.mark.asyncio
    async def test_reconfigure_no_input_shows_form_with_email(self):
        """Calling reconfigure with no input shows the form with the stored email."""
        flow = _make_reconfigure_flow(email="user@example.com")

        result = await flow.async_step_reconfigure(None)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        assert result["description_placeholders"] == {"email": "user@example.com"}
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_reconfigure_success_updates_entry(self):
        """A successful reconfigure updates the entry password and aborts with reconfigure_successful."""
        flow = _make_reconfigure_flow(email="test@example.com", password="oldpass")

        with _patch_konnect_client():
            result = await flow.async_step_reconfigure({CONF_PASSWORD: "newpass"})

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        flow.async_update_reload_and_abort.assert_called_once()
        _, kwargs = flow.async_update_reload_and_abort.call_args
        assert kwargs["data_updates"] == {CONF_PASSWORD: "newpass"}

    @pytest.mark.asyncio
    async def test_reconfigure_invalid_auth_shows_error(self):
        """An AndersenAuthError during reconfigure re-shows the form with invalid_auth."""
        flow = _make_reconfigure_flow()

        with _patch_konnect_client(auth_error=AndersenAuthError("bad password")):
            result = await flow.async_step_reconfigure({CONF_PASSWORD: "wrong"})

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}
        flow.async_update_reload_and_abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_reconfigure_cannot_connect_shows_error(self):
        """An AndersenConnectionError during reconfigure re-shows the form with cannot_connect."""
        flow = _make_reconfigure_flow()

        with _patch_konnect_client(auth_error=AndersenConnectionError("network down")):
            result = await flow.async_step_reconfigure({CONF_PASSWORD: "newpass"})

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
        flow.async_update_reload_and_abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_reconfigure_unknown_error_shows_error(self):
        """An unexpected exception during reconfigure re-shows the form with unknown."""
        flow = _make_reconfigure_flow()

        with patch("andersen_ev.config_flow.validate_input", AsyncMock(side_effect=Exception("boom"))):
            result = await flow.async_step_reconfigure({CONF_PASSWORD: "newpass"})

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}
        flow.async_update_reload_and_abort.assert_not_called()


class TestManifest:
    """Tests for the manifest.json declarations this feature relies on."""

    def test_single_config_entry_declared(self):
        """The manifest declares single_config_entry so HA blocks a second account at the platform level."""
        manifest = json.loads(MANIFEST_PATH.read_text())

        assert manifest["single_config_entry"] is True
