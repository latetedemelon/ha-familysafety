"""Microsoft Family Safety integration."""

import logging

from pyfamilysafety import FamilySafety
from pyfamilysafety.exceptions import HttpException, Unauthorized, AggregatorException

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady
)

from .const import AGG_ERROR, CONF_EXPR_DEFAULT, CONF_KEY_EXPR
from .coordinator import FamilySafetyCoordinator
from .config_entry import FamilySafetyConfigEntry

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: FamilySafetyConfigEntry) -> bool:
    """Create ConfigEntry."""
    _LOGGER.debug("Got request to setup entry.")
    try:
        familysafety = await FamilySafety.create(
            token=entry.options.get(
                "refresh_token", entry.data.get("refresh_token")),
            use_refresh_token=True,
            experimental=entry.options.get(CONF_KEY_EXPR, CONF_EXPR_DEFAULT))
    except Unauthorized as err:
        raise ConfigEntryAuthFailed from err
    except AggregatorException as err:
        _LOGGER.error(AGG_ERROR)
        raise ConfigEntryNotReady(AGG_ERROR) from err
    except HttpException as err:
        raise ConfigEntryNotReady(
            f"Error connecting to Family Safety: {err}") from err
    except Exception as err:
        _LOGGER.exception("Unexpected error setting up Family Safety")
        raise ConfigEntryNotReady(str(err)) from err

    _LOGGER.debug("Login successful, setting up coordinator.")
    entry.runtime_data = FamilySafetyCoordinator(
        hass,
        entry,
        familysafety,
        entry.options.get("update_interval", entry.data["update_interval"]))
    # no need to fetch initial data as this is already handled on creation

    async def update_listener(hass: HomeAssistant, entry: FamilySafetyConfigEntry):
        """Update listener."""
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FamilySafetyConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading config entry %s", entry.entry_id)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.api.api.end_session()
    return unload_ok
