"""Tests for integration setup and unload."""

from unittest.mock import AsyncMock, patch

from pyfamilysafety.exceptions import AggregatorException, Unauthorized

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState

from custom_components.family_safety.const import DOMAIN
from custom_components.family_safety.coordinator import FamilySafetyCoordinator


async def test_setup_and_unload_entry(hass, mock_config_entry, mock_familysafety):
    """A successful setup stores the coordinator and unload ends the session."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.family_safety.FamilySafety.create",
        AsyncMock(return_value=mock_familysafety),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert isinstance(mock_config_entry.runtime_data, FamilySafetyCoordinator)
    assert mock_config_entry.runtime_data.api is mock_familysafety

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    mock_familysafety.api.end_session.assert_awaited_once()


async def test_setup_entry_auth_failed_starts_reauth(hass, mock_config_entry):
    """An expired token fails setup and starts a reauth flow."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.family_safety.FamilySafety.create",
        AsyncMock(side_effect=Unauthorized()),
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert any(
        flow["context"]["source"] == config_entries.SOURCE_REAUTH for flow in flows)


async def test_setup_entry_retries_on_aggregator_error(hass, mock_config_entry):
    """A transient aggregator error puts the entry into retry, not failure."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.family_safety.FamilySafety.create",
        AsyncMock(side_effect=AggregatorException()),
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
