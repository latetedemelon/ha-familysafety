"""Tests for the data update coordinator."""

from unittest.mock import AsyncMock

import pytest
from pyfamilysafety.exceptions import (
    AggregatorException,
    HttpException,
    Unauthorized
)

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.family_safety.coordinator import FamilySafetyCoordinator


async def test_update_success(hass, mock_config_entry, mock_familysafety):
    """A successful poll calls the library update."""
    mock_config_entry.add_to_hass(hass)
    coordinator = FamilySafetyCoordinator(
        hass, mock_config_entry, mock_familysafety, 60)
    await coordinator._async_update_data()
    mock_familysafety.update.assert_awaited_once()


@pytest.mark.parametrize(
    ("side_effect", "expected"),
    [
        (Unauthorized(), ConfigEntryAuthFailed),
        (AggregatorException(), UpdateFailed),
        (HttpException("boom"), UpdateFailed),
    ],
)
async def test_update_errors(
        hass, mock_config_entry, mock_familysafety, side_effect, expected):
    """API errors map to the correct coordinator exceptions."""
    mock_config_entry.add_to_hass(hass)
    coordinator = FamilySafetyCoordinator(
        hass, mock_config_entry, mock_familysafety, 60)
    mock_familysafety.update = AsyncMock(side_effect=side_effect)
    with pytest.raises(expected):
        await coordinator._async_update_data()
