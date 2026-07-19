"""Tests for the BearerAuth requests.auth.AuthBase helper."""

from unittest.mock import MagicMock

from andersen_ev.konnect.bearerauth import BearerAuth


class TestBearerAuth:
    """Tests for BearerAuth."""

    def test_init_stores_token(self):
        """__init__() stores the provided token."""
        auth = BearerAuth("my-token")

        assert auth.token == "my-token"

    def test_call_sets_authorization_header(self):
        """__call__() sets the Authorization header and returns the request."""
        auth = BearerAuth("my-token")
        request = MagicMock()
        request.headers = {}

        result = auth(request)

        assert result is request
        assert request.headers["Authorization"] == "Bearer my-token"
