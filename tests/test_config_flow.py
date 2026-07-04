"""Tests for the config and options flows."""

from unittest.mock import AsyncMock, MagicMock, patch

from pyfamilysafety.exceptions import HttpException

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.family_safety.const import DOMAIN

from .conftest import MOCK_RESPONSE_URL

MOCK_USER_INPUT = {
    "response_url": MOCK_RESPONSE_URL,
    "update_interval": 60,
}


def _mock_authenticator() -> MagicMock:
    """Build a mocked pyfamilysafety Authenticator."""
    auth = MagicMock()
    auth.refresh_token = "new-refresh-token"
    auth.expires = None
    return auth


async def test_user_flow_success(hass):
    """A valid response URL creates an entry with the refresh token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.family_safety.config_flow.Authenticator.create",
        AsyncMock(return_value=_mock_authenticator()),
    ), patch(
        "custom_components.family_safety.async_setup_entry",
        AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT)
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["refresh_token"] == "new-refresh-token"
    assert result["data"]["update_interval"] == 60


async def test_user_flow_invalid_auth(hass):
    """An HTTP error from the authenticator shows the invalid_auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(
        "custom_components.family_safety.config_flow.Authenticator.create",
        AsyncMock(side_effect=HttpException("bad token")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass):
    """An unexpected error shows the cannot_connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(
        "custom_components.family_safety.config_flow.Authenticator.create",
        AsyncMock(side_effect=Exception("boom")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_flow(hass, mock_config_entry):
    """Reauth stores the new token in both data and options."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "custom_components.family_safety.config_flow.Authenticator.create",
        AsyncMock(return_value=_mock_authenticator()),
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_schedule_reload"
    ) as mock_reload:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"response_url": MOCK_RESPONSE_URL})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data["refresh_token"] == "new-refresh-token"
    assert mock_config_entry.options["refresh_token"] == "new-refresh-token"
    mock_reload.assert_called_once_with(mock_config_entry.entry_id)


async def test_reauth_flow_invalid_auth(hass, mock_config_entry):
    """A bad token during reauth re-shows the form with an error."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )

    with patch(
        "custom_components.family_safety.config_flow.Authenticator.create",
        AsyncMock(side_effect=HttpException("bad token")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"response_url": MOCK_RESPONSE_URL})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}
    assert mock_config_entry.data["refresh_token"] == "mock-refresh-token"


async def test_options_flow_auth_step(hass, setup_integration, mock_familysafety):
    """The options auth step saves a new token without crashing."""
    entry = setup_integration

    with patch(
        "custom_components.family_safety.config_flow.Authenticator.create",
        AsyncMock(return_value=MagicMock()),
    ), patch(
        "custom_components.family_safety.config_flow.FamilySafety",
        MagicMock(return_value=mock_familysafety),
    ), patch(
        "custom_components.family_safety.Authenticator.create",
        AsyncMock(return_value=MagicMock()),
    ), patch(
        "custom_components.family_safety.FamilySafety",
        MagicMock(return_value=mock_familysafety),
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.MENU

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "auth"})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "auth"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {"refresh_token": "updated-token", "update_interval": 120})
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["refresh_token"] == "updated-token"
    assert result["data"]["update_interval"] == 120
    assert entry.options["refresh_token"] == "updated-token"
