"""Tests for KonnectClient Cognito auth and device-key-aware token refresh."""
# pylint: disable=protected-access

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from andersen_ev.konnect.client import KonnectClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_srp_auth_response(device_key=None):
    """Return a minimal AWS SRP authentication response dict."""
    result = {
        "AuthenticationResult": {
            "IdToken": "test-id-token",
            "TokenType": "Bearer",
            "ExpiresIn": 3600,
            "RefreshToken": "test-refresh-token",
        }
    }
    if device_key is not None:
        result["AuthenticationResult"]["NewDeviceMetadata"] = {"DeviceKey": device_key}
    return result


def _make_cognito_refresh_response():
    """Return a minimal Cognito REFRESH_TOKEN_AUTH AuthenticationResult (no RefreshToken)."""
    return {
        "AuthenticationResult": {
            "IdToken": "refreshed-id-token",
            "TokenType": "Bearer",
            "ExpiresIn": 3600,
        }
    }


# ---------------------------------------------------------------------------
# authenticate_user() — device key capture & device confirmation
# ---------------------------------------------------------------------------


class TestAuthenticate:
    """Tests for authenticate_user() device key capture and device confirmation."""

    @pytest.mark.asyncio
    async def test_authenticate_captures_device_key_and_confirms_device(self):
        """authenticate_user() stores deviceKey and calls confirm_device on NewDeviceMetadata."""
        client = KonnectClient("user@example.com", "password")
        auth_response = _make_srp_auth_response(device_key="dk-1")

        mock_aws_srp = MagicMock()
        mock_aws_srp.authenticate_user.return_value = auth_response

        with patch("andersen_ev.konnect.client.AWSSRP", return_value=mock_aws_srp):
            with patch.object(
                client,
                "_KonnectClient__fetchUsername",
                new=AsyncMock(return_value="test-username"),
            ):
                await client.authenticate_user()

        assert client.deviceKey == "dk-1"
        assert client.token == "test-id-token"
        assert client.refreshToken == "test-refresh-token"
        mock_aws_srp.confirm_device.assert_called_once_with(auth_response)

    @pytest.mark.asyncio
    async def test_authenticate_no_device_metadata_leaves_device_key_none(self):
        """authenticate_user() leaves deviceKey as None when no NewDeviceMetadata present."""
        client = KonnectClient("user@example.com", "password")
        auth_response = _make_srp_auth_response()  # no NewDeviceMetadata

        mock_aws_srp = MagicMock()
        mock_aws_srp.authenticate_user.return_value = auth_response

        with patch("andersen_ev.konnect.client.AWSSRP", return_value=mock_aws_srp):
            with patch.object(
                client,
                "_KonnectClient__fetchUsername",
                new=AsyncMock(return_value="test-username"),
            ):
                await client.authenticate_user()

        assert client.deviceKey is None
        assert client.token == "test-id-token"
        mock_aws_srp.confirm_device.assert_not_called()

    @pytest.mark.asyncio
    async def test_authenticate_continues_when_confirm_device_fails(self):
        """authenticate_user() succeeds and logs a warning if confirm_device raises."""
        client = KonnectClient("user@example.com", "password")
        auth_response = _make_srp_auth_response(device_key="dk-warn")

        mock_aws_srp = MagicMock()
        mock_aws_srp.authenticate_user.return_value = auth_response
        mock_aws_srp.confirm_device.side_effect = Exception("confirm failed")

        with patch("andersen_ev.konnect.client.AWSSRP", return_value=mock_aws_srp):
            with patch.object(
                client,
                "_KonnectClient__fetchUsername",
                new=AsyncMock(return_value="test-username"),
            ):
                # Should NOT raise despite confirm_device failure
                await client.authenticate_user()

        # The token should still be set; deviceKey captured from NewDeviceMetadata
        assert client.token == "test-id-token"
        assert client.deviceKey == "dk-warn"


# ---------------------------------------------------------------------------
# refresh_token() — device-key-aware path and fallbacks
# ---------------------------------------------------------------------------


class TestRefreshToken:
    """Tests for refresh_token() device-key-aware refresh and fallback behaviour."""

    @pytest.mark.asyncio
    async def test_refresh_uses_device_key(self):
        """refresh_token() calls REFRESH_TOKEN_AUTH with DEVICE_KEY and updates token fields."""
        client = KonnectClient("user@example.com", "password")
        client.refreshToken = "rt"
        client.deviceKey = "dk"

        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.return_value = _make_cognito_refresh_response()

        with patch("andersen_ev.konnect.client.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_cognito
            await client.refresh_token()

        # Verify the Cognito client was created for the correct region
        mock_boto3.client.assert_called_once_with("cognito-idp", region_name="eu-west-1")

        # Verify initiate_auth was called with the expected parameters
        mock_cognito.initiate_auth.assert_called_once_with(
            ClientId="23s0olnnniu5472ons0d9uoqt9",
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": "rt", "DEVICE_KEY": "dk"},
        )

        # Verify token fields were updated
        assert client.token == "refreshed-id-token"
        assert client.tokenType == "Bearer"
        assert client.tokenExpiresIn == 3600

    @pytest.mark.asyncio
    async def test_dead_refresh_token_falls_back_to_full_auth(self):
        """refresh_token() falls back to authenticate_user() on NotAuthorizedException."""
        client = KonnectClient("user@example.com", "password")
        client.refreshToken = "expired-rt"
        client.deviceKey = "dk"

        not_authorized = ClientError(
            {"Error": {"Code": "NotAuthorizedException", "Message": "Invalid Refresh Token"}},
            "InitiateAuth",
        )

        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.side_effect = not_authorized

        with patch("andersen_ev.konnect.client.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_cognito
            with patch.object(client, "authenticate_user", new_callable=AsyncMock) as mock_full_auth:
                await client.refresh_token()

        mock_full_auth.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_token_or_device_key_falls_back_to_full_auth(self):
        """refresh_token() falls back immediately when refreshToken or deviceKey is absent."""
        client = KonnectClient("user@example.com", "password")
        # Both are None by default — guard should trigger before any Cognito call

        with patch.object(client, "authenticate_user", new_callable=AsyncMock) as mock_full_auth:
            await client.refresh_token()

        mock_full_auth.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_only_device_key_missing_falls_back_to_full_auth(self):
        """refresh_token() falls back when refreshToken is set but deviceKey is None."""
        client = KonnectClient("user@example.com", "password")
        client.refreshToken = "rt"
        # deviceKey remains None

        with patch.object(client, "authenticate_user", new_callable=AsyncMock) as mock_full_auth:
            await client.refresh_token()

        mock_full_auth.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_refresh_token_not_rotated_when_absent_from_response(self):
        """refresh_token() keeps the existing refreshToken when Cognito does not return a new one."""
        client = KonnectClient("user@example.com", "password")
        client.refreshToken = "original-rt"
        client.deviceKey = "dk"

        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.return_value = _make_cognito_refresh_response()

        with patch("andersen_ev.konnect.client.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_cognito
            await client.refresh_token()

        # The stored refresh token must NOT have been overwritten
        assert client.refreshToken == "original-rt"

    @pytest.mark.asyncio
    async def test_refresh_updates_refresh_token_if_rotated(self):
        """refresh_token() replaces refreshToken when Cognito unexpectedly rotates it."""
        client = KonnectClient("user@example.com", "password")
        client.refreshToken = "old-rt"
        client.deviceKey = "dk"

        rotated_response = {
            "AuthenticationResult": {
                "IdToken": "new-id-token",
                "TokenType": "Bearer",
                "ExpiresIn": 3600,
                "RefreshToken": "rotated-rt",
            }
        }

        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.return_value = rotated_response

        with patch("andersen_ev.konnect.client.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_cognito
            await client.refresh_token()

        assert client.refreshToken == "rotated-rt"

    @pytest.mark.asyncio
    async def test_non_auth_client_error_is_reraised(self):
        """refresh_token() re-raises ClientError codes other than NotAuthorizedException."""
        client = KonnectClient("user@example.com", "password")
        client.refreshToken = "rt"
        client.deviceKey = "dk"

        service_error = ClientError(
            {"Error": {"Code": "TooManyRequestsException", "Message": "slow down"}},
            "InitiateAuth",
        )

        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.side_effect = service_error

        with patch("andersen_ev.konnect.client.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_cognito
            with pytest.raises(ClientError):
                await client.refresh_token()
