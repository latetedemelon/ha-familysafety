"""Family Safety data hub."""

import asyncio
import logging
from datetime import timedelta

from pyfamilysafety import FamilySafety
from pyfamilysafety.exceptions import (
    AggregatorException,
    HttpException,
    Unauthorized
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import AGG_ERROR, NAME

_LOGGER = logging.getLogger(__name__)

class FamilySafetyCoordinator(DataUpdateCoordinator):
    """Family safety data updater."""

    def __init__(self,
                 hass: HomeAssistant,
                 config_entry: ConfigEntry,
                 family_safety: FamilySafety,
                 update_interval: int=60) -> None:
        """Init the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=NAME,
            config_entry=config_entry,
            update_interval=timedelta(seconds=update_interval)
        )
        self.api: FamilySafety = family_safety

    async def _async_update_data(self):
        """Fetch and update data from the API."""
        try:
            async with asyncio.timeout(50):
                return await self.api.update()
        except Unauthorized as err:
            raise ConfigEntryAuthFailed("Family Safety token expired") from err
        except AggregatorException as err:
            raise UpdateFailed(AGG_ERROR) from err
        except HttpException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
