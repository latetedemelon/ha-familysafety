"""Fixtures for the Microsoft Family Safety tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.family_safety.const import DOMAIN

MOCK_USER_ID = "1234"
MOCK_RESPONSE_URL = "https://login.live.com/oauth20_desktop.srf?code=test"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


def _mock_application(app_id: str, name: str, usage: int) -> MagicMock:
    """Build a mocked pyfamilysafety Application."""
    app = MagicMock()
    app.app_id = app_id
    app.name = name
    app.usage = usage
    app.blocked = False
    app.icon = None
    app.policy = "Allowed"
    app.block_app = AsyncMock()
    app.unblock_app = AsyncMock()
    return app


@pytest.fixture
def mock_account():
    """Return a mocked pyfamilysafety Account."""
    account = MagicMock()
    account.user_id = MOCK_USER_ID
    account.first_name = "Test"
    account.surname = "Child"
    account.role = "User"
    account.today_screentime_usage = 1_800_000  # 30 minutes in ms
    account.today_restriction = 3_600_000  # 60 minutes in ms
    account.average_screentime_usage = 0
    account.screentime_usage = {}
    account.blocked_platforms = []
    account.devices = []
    account.experimental = False
    account.account_balance = 5.0
    account.account_currency = "USD"
    applications = [
        _mock_application("app1", "Minecraft", 10),
        _mock_application("app2", "Roblox", 20),
    ]
    account.applications = applications
    account.get_application = MagicMock(
        side_effect=lambda app_id: {a.app_id: a for a in applications}.get(app_id))
    account.override_device = AsyncMock()
    account.update = AsyncMock()
    return account


@pytest.fixture
def mock_familysafety(mock_account):
    """Return a mocked pyfamilysafety FamilySafety."""
    familysafety = MagicMock()
    familysafety.accounts = [mock_account]
    familysafety.get_account = MagicMock(return_value=mock_account)
    familysafety.pending_requests = []
    familysafety.experimental = False
    familysafety.update = AsyncMock()
    familysafety.approve_pending_request = AsyncMock()
    familysafety.deny_pending_request = AsyncMock()
    familysafety.api = MagicMock()
    familysafety.api.end_session = AsyncMock()
    return familysafety


@pytest.fixture
def mock_config_entry():
    """Return a mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Microsoft Family Safety",
        data={
            "response_url": MOCK_RESPONSE_URL,
            "refresh_token": "mock-refresh-token",
            "update_interval": 60,
        },
        options={
            "tracked_applications": ["app1", "app2"],
        },
    )


@pytest.fixture
async def setup_integration(hass, mock_config_entry, mock_familysafety):
    """Set up the integration with a mocked API."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.family_safety.FamilySafety.create",
        AsyncMock(return_value=mock_familysafety),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    return mock_config_entry
